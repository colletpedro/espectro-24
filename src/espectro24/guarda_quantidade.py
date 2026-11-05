"""Guarda de quantidade (2026-11-05): reescrita DETERMINÍSTICA das expressões de
quantidade de `exemplo_parafraseado`.

Por quê: o treinado (Qwen3-8B + LoRA) usou palavra de quantidade em 82,4% dos
exemplos (o publicado, em 56,7%; ver `finetune/RESULTADO_FASE4.md`, C3). Essas
palavras ("muitos espectadores acham", "várias reviews destacam") afirmam uma
prevalência que o modelo não mediu: a contagem de menções vem do LLM e a barra
do tema já diz o quanto o tema pesa.

Regras (decisão do dono):
- remove o quantificador ou troca por forma NÃO quantitativa; os rótulos de
  quantidade da lista congelada nunca são reintroduzidos (a lista tem até
  "há quem" e "parte do público": a guarda não os emite);
- NUNCA introduz número; nunca muda o sentido de avaliação;
- NUNCA remove, junta ou reordena bullets: a guarda só reescreve o texto de um
  `exemplo_parafraseado` (o invariante de mesma quantidade de bullets entre
  grupos não depende dela);
- texto que não puder ser reescrito com segurança fica EXATAMENTE como veio e
  é devolvido em `pendentes` (nenhum fallback é aplicado aqui; a decisão de
  uma nova chamada do bucket é do dono).

A detecção usa a lista CONGELADA do M1 (`palavras_quantidade.txt`, sha256
`a7fcd5a5…`, a mesma de `finetune/metricas/palavras_quantidade.txt`), com a
mesma regra de casamento (sem caixa, palavra inteira, sem dobra de acento).
A reescrita é por regras explícitas por expressão; tudo fora delas é
"sem reescrita".
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

LISTA = Path(__file__).with_name("palavras_quantidade.txt")
LISTA_SHA256 = "a7fcd5a5663c3ebdc0112b27bd8821c839d47de86673ef4ebdea83c0524c14af"

_BORDA_ANTES = r"(?<!\w)"
_BORDA_DEPOIS = r"(?!\w)"
_PALAVRA = r"[^\W\d_]+(?:-[^\W\d_]+)*"


def carregar_lista(caminho: Path = LISTA) -> list[str]:
    fora = [ln.strip() for ln in Path(caminho).read_text(encoding="utf-8").split("\n")]
    fora = [ln for ln in fora if ln and not ln.startswith("#")]
    if len(fora) != len(set(fora)):
        raise ValueError("expressão repetida na lista")
    return fora


def compilar(expressoes: list[str]) -> re.Pattern:
    alt = sorted((re.escape(e).replace(r"\ ", " ") for e in expressoes), key=len, reverse=True)
    return re.compile(_BORDA_ANTES + "(?:" + "|".join(alt) + ")" + _BORDA_DEPOIS, re.IGNORECASE)


_PADRAO = compilar(carregar_lista())


def tem_quantidade(texto: str) -> bool:
    """O M1 (mesma regra de `scripts/finetune/metricas.py`)."""
    return bool(_PADRAO.search(texto or ""))


@dataclass
class Reescrita:
    texto: str                               # texto final (igual ao original se nada mudou)
    original: str
    alterado: bool = False
    regras: list[str] = field(default_factory=list)       # uma por edição aplicada
    pendentes: list[str] = field(default_factory=list)    # expressões que ficaram (com o motivo)

    @property
    def residual(self) -> bool:
        """O texto final ainda casa com a lista (conta no M1)."""
        return tem_quantidade(self.texto)


# --------------------------------------------------------------------------
# Léxico (listas fechadas; o que não está aqui NÃO é reescrito)
# --------------------------------------------------------------------------

# Quem fala nas reviews (plural).
_PESSOAS = frozenset("""reviews críticas críticos espectadores comentários pessoas usuários
fãs avaliações opiniões resenhas leitores comentaristas internautas cinéfilos avaliadores
revisões""".split())

# Palavras que, logo depois do quantificador, mostram que ele NÃO é determinante
# de um substantivo simples (ou que a quantidade é medida: tempo, vezes).
_NAO_SUBSTANTIVO = frozenset("""de do da dos das deles delas desses dessas destes destas
desse dessa deste desta nos nas num numa em com por para sem sob sobre entre até que e ou mas
mais menos tão muito bem outros outras outro outra todos todas tantos tantas pouco poucos
poucas vezes minutos segundos horas dias anos semanas meses décadas séculos instantes
momentos""".split())
# "momentos" fica fora do corte acima só se o quantificador for "alguns/algumas":
_NAO_SUBSTANTIVO_FORTE = _NAO_SUBSTANTIVO - {"momentos"}

_QUANT_PLURAL = {
    "muitos": "m", "muitas": "f", "vários": "m", "várias": "f", "diversos": "m",
    "diversas": "f", "alguns": "m", "algumas": "f", "inúmeros": "m", "inúmeras": "f",
    "numerosos": "m", "numerosas": "f",
}
_EXISTENCIAIS = {"alguns": "certos", "algumas": "certas"}
# Substantivos de posição no filme: com quantificador, a troca é por "certos/certas"
# ("em vários momentos" → "em certos momentos"), forma que a lista congelada
# deixa de fora de propósito (posição no filme, não prevalência entre reviews).
_POSICIONAIS = frozenset("momentos pontos trechos passagens".split())

# Verbos de fala das reviews, na 3ª pessoa do SINGULAR do presente (o plural é
# o singular + "m", salvo as irregulares). Lista fechada: verbo fora dela =
# sem reescrita.
_VERBOS_SG = frozenset("""acha aponta menciona destaca elogia critica considera descreve relata
comenta reclama nota diz reconhece aprecia ressalta cita indica sugere afirma acusa compara
questiona vê sente classifica avalia lamenta defende observa enfatiza valoriza reforça associa
entende percebe compreende interpreta lê atribui acredita aprova rejeita recomenda prefere
aborda expressa vincula cobra exalta aplaude censura condena teme duvida admite aceita
reprova contesta ressente""".split())
_ESPECIAIS = {   # sg: (presente pl, subjuntivo sg, subjuntivo pl, pretérito pl, gerúndio)
    "diz": ("dizem", "diga", "digam", "disseram", "dizendo", "dizerem"),
    "vê": ("veem", "veja", "vejam", "viram", "vendo", "verem"),
    "lê": ("leem", "leia", "leiam", "leram", "lendo", "lerem"),
    "sente": ("sentem", "sinta", "sintam", "sentiram", "sentindo", "sentirem"),
    "sugere": ("sugerem", "sugira", "sugiram", "sugeriram", "sugerirem"[:0] + "sugerindo", "sugerirem"),
    "prefere": ("preferem", "prefira", "prefiram", "preferiram", "preferindo", "preferirem"),
    "ressente": ("ressentem", "ressinta", "ressintam", "ressentiram", "ressentindo", "ressentirem"),
    "atribui": ("atribuem", "atribua", "atribuam", "atribuíram", "atribuindo", "atribuírem"),
    "admite": ("admitem", "admita", "admitam", "admitiram", "admitindo", "admitirem"),
}


def _formas(v: str) -> tuple[str, ...] | None:
    """(presente pl, subj. sg, subj. pl, pretérito pl, gerúndio) de um verbo da
    lista fechada, a partir da 3ª pessoa do singular do presente."""
    if v in _ESPECIAIS:
        return _ESPECIAIS[v]
    if v not in _VERBOS_SG:
        return None
    radical = v[:-1]
    if v.endswith("a"):                                        # 1ª conjugação
        r = radical
        for fim, troca in (("ç", "c"), ("c", "qu"), ("g", "gu")):
            if r.endswith(fim):
                r = r[:-len(fim)] + troca
                break
        return (v + "m", r + "e", r + "em", radical + "aram", radical + "ando",
                radical + "arem")
    if v.endswith("e"):                                        # 2ª conjugação
        r = radical
        for fim, troca in (("c", "ç"), ("g", "j")):
            if r.endswith(fim):
                r = r[:-len(fim)] + troca
                break
        return (v + "m", r + "a", r + "am", radical + "eram", radical + "endo",
                radical + "erem")
    return None


def _plural_do_verbo(v: str) -> str | None:
    f = _formas(v.lower())
    return f[0] if f else None


_VERBOS_PL = frozenset(filter(None, (_plural_do_verbo(v) for v in _VERBOS_SG | set(_ESPECIAIS))))
# toda forma plural aceita depois de um quantificador pronominal ("muitos acham",
# "embora alguns considerem", "alguns comentaram", "muitos elogiando")
_FORMAS_PL = frozenset(f for v in (_VERBOS_SG | set(_ESPECIAIS)) for f in (_formas(v) or ())
                       if f.endswith(("m", "ndo")))
_PRET_SG = {}
for _v in (_VERBOS_SG | set(_ESPECIAIS)):
    _f = _formas(_v)
    if _f and _v not in _ESPECIAIS:
        _PRET_SG[_v[:-1] + ("ou" if _v.endswith("a") else "eu")] = _f[3]
_PRET_SG.update({"disse": "disseram", "viu": "viram", "leu": "leram", "sentiu": "sentiram",
                 "sugeriu": "sugeriram", "preferiu": "preferiram", "admitiu": "admitiram"})
_SUBJ_SG = {f[1]: f[0] for v in (_VERBOS_SG | set(_ESPECIAIS)) if (f := _formas(v))}

_ADJ_GRUPO = frozenset("positivas negativas medianas positivos negativos medianos".split())

_SUBST_RECORRENTE = frozenset("""problema problemas crítica críticas queixa queixas reclamação
reclamações elogio elogios comentário comentários observação observações""".split())
_NEGACAO = frozenset("não nem nunca jamais sem pouco pouca tão mais menos muito bem raramente".split())
_CONJ_INICIO = frozenset("e mas enquanto embora porém contudo que pois já".split())


# --------------------------------------------------------------------------
# Utilidades de texto
# --------------------------------------------------------------------------

def _palavra_seguinte(texto: str, i: int) -> tuple[str, int, int] | None:
    """Próxima palavra depois de `i`, separada só por UM espaço (sem pontuação)."""
    m = re.match(r" (" + _PALAVRA + ")", texto[i:])
    return (m.group(1), i + m.start(1), i + m.end(1)) if m else None


def _palavra_anterior(texto: str, i: int) -> tuple[str, int] | None:
    """Palavra imediatamente antes de `i`, separada só por UM espaço."""
    m = re.search(r"(" + _PALAVRA + r") $", texto[:i])
    return (m.group(1), m.start(1)) if m else None


def _inicio_de_frase(texto: str, i: int) -> bool:
    """`i` abre uma frase (início do texto ou depois de ". ", "! ", "? ")."""
    ant = texto[:i].rstrip(" ")
    return not ant or ant[-1] in ".!?\n"


def _maiuscula(texto: str, i: int) -> str:
    """Primeira letra a partir de `i` em maiúscula."""
    m = re.compile(r"[^\W\d_]").search(texto, i)
    if not m:
        return texto
    return texto[:m.start()] + m.group(0).upper() + texto[m.end():]


def _frase_de(texto: str, i: int) -> str:
    ini = max(texto.rfind(". ", 0, i), texto.rfind("! ", 0, i), texto.rfind("? ", 0, i))
    ini = 0 if ini < 0 else ini + 2
    fim = len(texto)
    for p in (". ", "! ", "? "):
        j = texto.find(p, i)
        if j >= 0:
            fim = min(fim, j)
    return texto[ini:fim]


def _tem_outros(texto: str, i: int) -> bool:
    return bool(re.search(r"(?<!\w)(outros|outras|enquanto outr)", _frase_de(texto, i), re.I))


def _remover_trecho(texto: str, ini: int, fim: int, cap: bool | None = None) -> str:
    """Remove texto[ini:fim] (já com o espaço que o acompanha). Se a remoção abre
    a frase, a próxima letra vira maiúscula."""
    abre = _inicio_de_frase(texto, ini) if cap is None else cap
    novo = texto[:ini] + texto[fim:]
    return _maiuscula(novo, ini) if abre else novo


# --------------------------------------------------------------------------
# Regras. Cada regra devolve (novo_texto, posição_de_retomada, nome) ou
# (None, motivo) quando não há reescrita segura.
# --------------------------------------------------------------------------

def _regra_quant_plural(t: str, m: re.Match):
    exp = m.group(0)
    low = exp.lower()
    g = _QUANT_PLURAL[low]
    s, e = m.start(), m.end()
    ant = _palavra_anterior(t, s)
    if ant and (ant[0].lower() in _NEGACAO or ant[0].lower() in
                {"os", "as", "dos", "das", "nos", "nas", "aos", "às", "outros", "outras", "tantos", "tantas"}):
        return None, "precedido de artigo/negação/'outros'"
    seg = _palavra_seguinte(t, e)
    if ant and ant[0].lower() in {"por", "para"} and low in ("alguns", "muitos", "algumas", "muitas") \
            and (not seg or seg[0].lower() in {"como", ".", "a", "o"} or t[e:e + 1] in ".,;:"):
        sujeito = "espectadores" if g == "m" else "reviews"
        return t[:s] + sujeito + t[e:], s + len(sujeito), "por/para+pronome"
    if not seg:
        return None, "quantificador sem substantivo logo depois"
    w1, _, w1_fim = seg
    w1l = w1.lower()
    if w1l in _PESSOAS:
        return _remover_trecho(t, s, e + 1), s, "quant+pessoas"
    # forma pronominal ("muitos acham"): sujeito oculto
    if w1l == "vezes" and low == "muitas":
        return _regra_frequencia(t, m, fim=w1_fim)
    if w1l in {"também", "ainda"}:           # "algumas também mencionam"
        seg2 = _palavra_seguinte(t, w1_fim)
        if seg2 and seg2[0].lower() in _FORMAS_PL:
            sujeito = "espectadores" if g == "m" else "reviews"
            novo = t[:s] + sujeito + t[e:]
            return (_maiuscula(novo, s) if _inicio_de_frase(t, s) else novo), s + len(sujeito), "quant+também+verbo"
    if w1l in {"a", "o", "as", "os"}:        # "alguns a consideram"
        seg2 = _palavra_seguinte(t, w1_fim)
        if seg2 and seg2[0].lower() in _FORMAS_PL:
            sujeito = "espectadores" if g == "m" else "reviews"
            novo = t[:s] + sujeito + t[e:]
            return (_maiuscula(novo, s) if _inicio_de_frase(t, s) else novo), s + len(sujeito), "quant+clítico+verbo"
    if w1l in _FORMAS_PL or (re.fullmatch(r"[^\W\d_]+ndo-(?:a|o|as|os|se|lhe|lhes)", w1l)
                             and w1l.split("-")[0] in _FORMAS_PL):
        sujeito = "espectadores" if g == "m" else "reviews"
        novo = t[:s] + sujeito + t[e:]
        return (_maiuscula(novo, s) if _inicio_de_frase(t, s) else novo), s + len(sujeito), "quant+verbo"
    if w1l in _POSICIONAIS:                   # "em vários momentos" → "em certos momentos"
        sub = "certos" if g == "m" else "certas"
        novo = t[:s] + (sub.capitalize() if exp[0].isupper() else sub) + t[e:]
        return novo, s + len(sub), "quant→certos+posicional"
    limite = _NAO_SUBSTANTIVO_FORTE if low in _EXISTENCIAIS else _NAO_SUBSTANTIVO
    if w1l in limite or not w1l.endswith("s") or len(w1l) < 4:
        return None, f"seguido de '{w1l}' (não é substantivo plural simples)"
    if re.match(r"\d", t[e + 1:]):
        return None, "seguido de número"
    if low in _EXISTENCIAIS:
        sub = _EXISTENCIAIS[low]
        novo = t[:s] + (sub.capitalize() if exp[0].isupper() else sub) + t[e:]
        return novo, s + len(sub), "alguns→certos+substantivo"
    return _remover_trecho(t, s, e + 1), s, "quant+substantivo"


def _regra_certos(t: str, m: re.Match):
    s, e = m.start(), m.end()
    palavras = m.group(0).split(" ")
    nome = palavras[1]
    novo = t[:s] + nome[0].upper() + nome[1:] + t[e:] if _inicio_de_frase(t, s) else t[:s] + nome + t[e:]
    return novo, s + len(nome), "certas+pessoas"


_PREP_PARTITIVO = {
    "parte do público": "espectadores", "parte das reviews": "reviews",
    "parte das críticas": "críticas", "parte dos espectadores": "espectadores",
    "parte das pessoas": "pessoas", "parte dos comentários": "comentários",
    "parte do grupo": "espectadores do grupo", "parte deste grupo": "espectadores deste grupo",
    "parte desse grupo": "espectadores desse grupo",
}


def _sujeito_de_frase(t: str, s: int) -> bool:
    """O sintagma que começa em `s` está em posição de sujeito: abre a frase ou
    vem depois de vírgula/conjunção."""
    if _inicio_de_frase(t, s):
        return True
    ant = _palavra_anterior(t, s)
    if ant and ant[0].lower() in _CONJ_INICIO:
        return True
    return bool(re.search(r", $", t[:s]))


def _verbo_depois(t: str, i: int):
    """Verbo (3sg) da lista logo depois de `i`, aceitando um "se" antes. Devolve
    (ini, fim, plural, tem_se)."""
    m = re.match(r" (se )?(" + _PALAVRA + ")", t[i:])
    if not m:
        return None
    v = m.group(2)
    if m.group(1):
        raise_se = True
        base = v.lower()
        # "se incomoda": reflexivos sem lista → só os conhecidos
        if base not in {"incomoda", "sente", "incomodou", "ressente"}:
            return None
        plural = base + "m"
    else:
        raise_se = False
        plural = _plural_do_verbo(v) or _PRET_SG.get(v.lower())
        if not plural:
            return None
    return i + m.start(2), i + m.end(2), plural, raise_se


def _regra_parte(t: str, m: re.Match):
    s, e = m.start(), m.end()
    sub = _PREP_PARTITIVO.get(m.group(0).lower())
    if not sub:
        return None, "partitivo sem forma de troca"
    ant = _palavra_anterior(t, s)
    if ant and ant[0].lower() == "para":                   # "para parte do público"
        return t[:s] + sub + t[e:], s + len(sub), "parte→plural (complemento)"
    if not _sujeito_de_frase(t, s):
        return None, "'parte' fora de posição de sujeito"
    adj = re.compile(r"(?: (?:" + "|".join(_ADJ_GRUPO) + r"))?").match(t, e)
    e2 = adj.end() if adj else e
    vb = _verbo_depois(t, e2)
    if not vb:
        return None, "verbo seguinte fora da lista"
    vi, vf, plural, _ = vb
    novo = t[:s] + sub + t[e:vi] + plural + t[vf:]
    return (_maiuscula(novo, s) if _inicio_de_frase(t, s) else novo), s + len(sub), "parte→plural"


def _regra_maioria(t: str, m: re.Match):
    """"A maioria das reviews positivas elogia" → "As reviews positivas elogiam"."""
    s, e = m.start(), m.end()
    ant = _palavra_anterior(t, s)
    expr = m.group(0).lower()
    ini = s
    if expr == "maioria":
        if not ant or ant[0].lower() != "a":
            return None, "'maioria' sem artigo de sujeito"
        ini = ant[1]
    if not _sujeito_de_frase(t, ini):
        return None, "'maioria' fora de posição de sujeito"
    r = re.compile(r" (d[ao]s) (" + _PALAVRA + ")((?: " + "(?:" + "|".join(_ADJ_GRUPO) + "))?"
                   r"(?: (?:deste|desse) grupo)?)", re.I).match(t, e)
    if not r:
        return None, "sintagma depois de 'maioria' fora do padrão"
    noun = r.group(2)
    if noun.lower() not in _PESSOAS:
        return None, f"'{noun}' não é substantivo de pessoa"
    vb = _verbo_depois(t, r.end())
    if not vb:
        return None, "verbo seguinte fora da lista"
    vi, vf, plural, _ = vb
    art = "os" if r.group(1).lower() == "dos" else "as"
    novo = t[:ini] + art + " " + noun + r.group(3) + t[r.end():vi] + plural + t[vf:]
    return (_maiuscula(novo, ini) if _inicio_de_frase(t, ini) else novo), ini + len(art), "maioria→plural"


def _regra_numero_de(t: str, m: re.Match):
    """"Um número significativo de reviews relatam" → "Reviews relatam"."""
    s, e = m.start(), m.end()
    r = re.compile(r" de (" + _PALAVRA + ")").match(t, e)
    if not r or r.group(1).lower() not in _PESSOAS:
        return None, "'número de' sem substantivo de pessoa"
    seg = _palavra_seguinte(t, r.end())
    if not seg or not (seg[0].lower() in _VERBOS_PL or seg[0].lower() in _ADJ_GRUPO):
        return None, "verbo seguinte fora da lista"
    ant = _palavra_anterior(t, s)
    ini = s
    novo = t[:ini] + t[r.start(1):]
    return (_maiuscula(novo, ini) if _inicio_de_frase(t, ini) else novo), ini, "número de→plural"


def _regra_quase_todos(t: str, m: re.Match):
    s, e = m.start(), m.end()
    seg = _palavra_seguinte(t, e)
    if not seg or seg[0].lower() not in {"os", "as"}:
        return None, "'quase todos' sem artigo"
    seg2 = _palavra_seguinte(t, seg[2])
    if not seg2 or seg2[0].lower() not in _PESSOAS:
        return None, "'quase todos' sem substantivo de pessoa"
    return _remover_trecho(t, s, e + 1), s, "quase todos→artigo"


def _regra_metade(t: str, m: re.Match):
    s, e = m.start(), m.end()
    expr = m.group(0).lower()
    if expr in ("cerca de metade", "quase metade"):
        r = re.compile(r" d([ao]s) (" + _PALAVRA + ")").match(t, e)
        if not r or r.group(2).lower() not in _PESSOAS:
            return None, "'metade' sem substantivo de pessoa"
        fim_sn = r.end()
        noun = r.group(2)
    else:
        sub = {"metade do grupo": "espectadores do grupo", "metade das reviews": "reviews",
               "metade dos espectadores": "espectadores"}[expr]
        noun, fim_sn = sub, e
    if not _sujeito_de_frase(t, s):
        return None, "'metade' fora de posição de sujeito"
    seg = _palavra_seguinte(t, fim_sn)
    if not seg:
        return None, "sem verbo depois de 'metade'"
    v = seg[0].lower()
    if v in _VERBOS_PL:
        resto = t[fim_sn:]
    elif v in _VERBOS_SG:
        resto = t[fim_sn:seg[1]] + _plural_do_verbo(v) + t[seg[2]:]
    else:
        return None, "verbo seguinte fora da lista"
    novo = t[:s] + noun + resto
    return (_maiuscula(novo, s) if _inicio_de_frase(t, s) else novo), s + len(noun), "metade→plural"


def _regra_frequencia(t: str, m: re.Match, fim: int | None = None):
    s, e = m.start(), (fim if fim is not None else m.end())
    ant = _palavra_anterior(t, s)
    if ant and ant[0].lower() in _NEGACAO:
        return None, "frequência sob negação/comparação"
    # janela de negação anterior (até 4 palavras antes)
    janela = re.findall(_PALAVRA, t[max(0, s - 40):s].lower())[-4:]
    if any(w in {"não", "nem", "nunca", "jamais"} for w in janela):
        return None, "negação na janela anterior"
    if fim is None and m.group(0).lower() in ("recorrente", "recorrentes"):
        if not ant or ant[0].lower() in {"é", "são", "como", "sendo", "ser", "foi", "foram", "tão", "bem"}:
            return None, "'recorrente' predicativo"
        if ant[0].lower() not in _SUBST_RECORRENTE:
            return None, "'recorrente' depois de substantivo fora da lista"
    depois = t[e:e + 1]
    # vírgulas ao redor: ", frequentemente," → ","
    if t[:s].endswith(", ") and depois == ",":
        novo = t[:s - 2] + t[e + 1:]            # ", frequentemente, " → " "
        return novo, s - 2, "frequência (parentética)"
    if _inicio_de_frase(t, s):
        if depois == ",":
            return _remover_trecho(t, s, e + 2, cap=True), s, "frequência (abre a frase)"
        if depois == " ":
            return _remover_trecho(t, s, e + 1, cap=True), s, "frequência (abre a frase)"
        return None, "frequência no início sem continuação"
    if depois == " ":
        return t[:s] + t[e + 1:], s, "frequência"
    if depois in ".,;:!?" or depois == "":
        if t[:s].endswith(" "):
            return t[:s - 1] + t[e:], s - 1, "frequência (fim de oração)"
    return None, "frequência em posição não prevista"


def _regra_ha_quem(t: str, m: re.Match):
    """"Há quem ache que…" → "Espectadores acham que…"."""
    s, e = m.start(), m.end()
    ant = _palavra_anterior(t, s)
    if ant and ant[0].lower() in {"não", "nem", "sem", "quase"}:
        return None, "'há quem' sob negação"
    seg = _palavra_seguinte(t, e)
    if not seg or seg[0].lower() not in _SUBJ_SG:
        return None, "verbo depois de 'há quem' fora da lista"
    pres = _SUBJ_SG[seg[0].lower()]
    novo = t[:s] + "espectadores " + pres + t[seg[2]:]
    return (_maiuscula(novo, s) if _inicio_de_frase(t, s) else novo), s + len("espectadores "), "há quem→plural"


def _despachar(exp: str):
    low = exp.lower()
    if low == "há quem":
        return _regra_ha_quem
    if low in _QUANT_PLURAL:
        return _regra_quant_plural
    if low in ("certas reviews", "certas críticas", "certos espectadores", "certos comentários"):
        return _regra_certos
    if low in _PREP_PARTITIVO:
        return _regra_parte
    if low in ("maioria", "grande parte", "boa parte", "maior parte"):
        return _regra_maioria
    if low in ("um número considerável", "um número significativo", "um número expressivo",
               "um bom número"):
        return _regra_numero_de
    if low in ("quase todos", "quase todas", "praticamente todos", "praticamente todas"):
        return _regra_quase_todos
    if low in ("cerca de metade", "quase metade", "metade do grupo", "metade das reviews",
               "metade dos espectadores"):
        return _regra_metade
    if low in ("frequentemente", "com frequência", "recorrente", "recorrentes", "recorrentemente"):
        return _regra_frequencia
    return None


_SEM_REGRA = "sem regra segura (expressão com sentido próprio ou fora dos padrões)"


def _limpar(t: str) -> str:
    t = re.sub(r"  +", " ", t)
    t = re.sub(r" ([,.;:!?])", r"\1", t)
    return t


def reescrever(texto: str) -> Reescrita:
    """Reescreve as expressões de quantidade que têm regra segura. Idempotente
    (aplicar de novo ao resultado não muda nada)."""
    original = texto or ""
    t = original
    r = Reescrita(texto=t, original=original)
    pos = 0
    ignoradas: set[str] = set()
    while True:
        m = _PADRAO.search(t, pos)
        if not m:
            break
        regra = _despachar(m.group(0))
        if regra is None:
            r.pendentes.append(f"{m.group(0).lower()}: {_SEM_REGRA}")
            pos = m.end()
            continue
        res = regra(t, m)
        if res[0] is None:
            r.pendentes.append(f"{m.group(0).lower()}: {res[1]}")
            pos = m.end()
            continue
        novo, a, b = res
        t = novo
        r.regras.append(b)
        pos = a
    t = _limpar(t) if t != original else t
    # Trava final: a guarda nunca introduz número, nunca cresce e nunca deixa o
    # texto vazio. Se algo disso acontecer, devolve o original intacto.
    if t != original:
        if (re.findall(r"\d+", t) != re.findall(r"\d+", original) or not t.strip()
                or len(t) > len(original) + 12):
            return Reescrita(texto=original, original=original,
                             pendentes=["guarda: trava final recusou a reescrita"])
        r.alterado = True
    r.texto = t
    return r
