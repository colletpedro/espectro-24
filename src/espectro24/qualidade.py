"""[§D2, v1.9.8] Verificações MECÂNICAS da prosa do narrador + resenha-speak.

Duas coisas vivem aqui, pela mesma razão:

1. **A blocklist de resenha-speak** (`dados/blocklist_resenha.txt`), dado
   VERSIONADO e fora do prompt. Fora do prompt por duas razões: o padrão de
   §3[D] (verificação em código é mais confiável que instrução — "não
   escreva clichê" é exatamente o tipo de regra que o modelo concorda e
   desobedece) e porque listar as expressões DENTRO do prompt as introduz no
   contexto, o que em vários modelos aumenta a chance de aparecerem.

2. **As checagens do briefing contra o texto** — número inventado, rótulo de
   peso faltando, ordem dos grupos, vocabulário do peso. São as que
   neutralizam, por construção, o risco histórico do Gemini de inflar
   contagem: qualquer número que não venha do briefing é reprovado
   mecanicamente, independentemente de o provider ser bem-comportado.

Uma ocorrência de resenha-speak não invalida a narrativa sozinha — é um
INDICADOR objetivo de prosa genérica, contado e reportado por modelo. As
demais flags são reprovação.
"""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent.parent
ARQ_BLOCKLIST = RAIZ / "dados" / "blocklist_resenha.txt"

# "das reviews"/"do público"/"dos espectadores" ao falar de PESO — o
# histograma é de NOTAS, e as duas populações são diferentes (invariante de
# vocabulário da v1.4.1, que continua sendo instrução no prompt e ganha aqui
# a checagem mecânica correspondente).
_PESO_PROIBIDO = re.compile(
    r"\b(?:d[aeo]s?)\s+(?:reviews|p[uú]blico|espectadores|cr[ií]ticos)\b",
    re.IGNORECASE)

_NUMERO = re.compile(r"\d+")


def _normalizar(s: str) -> str:
    """Minúsculo e sem acento — para a blocklist casar 'fôlego' com
    'folego' sem precisar de duas entradas."""
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def carregar_blocklist(caminho: Path | None = None) -> list[str]:
    """Expressões da blocklist, já normalizadas. Comentários (`#`) e linhas
    vazias são ignorados — o arquivo é documentação e dado ao mesmo tempo."""
    arq = caminho or ARQ_BLOCKLIST
    if not arq.exists():
        return []
    saida = []
    for linha in arq.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if linha and not linha.startswith("#"):
            saida.append(_normalizar(linha))
    return saida


def achar_resenha_speak(texto: str, blocklist: list[str] | None = None
                        ) -> list[dict]:
    """`[{expressao, n, trecho}]` para cada expressão encontrada.

    Devolve o TRECHO junto da contagem — mesma política de telemetria
    declarada do resto do projeto: o número sozinho não permite conferir se
    o achado é real.
    """
    exprs = carregar_blocklist() if blocklist is None else blocklist
    alvo = _normalizar(texto)
    achados = []
    for e in exprs:
        # fronteira de palavra nos dois lados: "um must" não casa "um mustang"
        pad = re.compile(rf"(?<!\w){re.escape(e)}(?!\w)")
        posicoes = [m.start() for m in pad.finditer(alvo)]
        if posicoes:
            i = posicoes[0]
            achados.append({"expressao": e, "n": len(posicoes),
                            "trecho": texto[max(0, i - 30):i + len(e) + 30]})
    return achados


def formato_invalido(bruto: str) -> bool:
    """Prosa que veio embrulhada em JSON ou markdown (§E2, v1.7.2)."""
    t = (bruto or "").strip()
    if not t:
        return True
    if t.startswith(("{", "[")):
        return True
    if "```" in t:
        return True
    primeiras = "\n".join(t.splitlines()[:3])
    return bool(re.search(r'"?(?:narrativa|text)"?\s*:', primeiras))


def tokens_numericos(texto: str) -> set[str]:
    return set(_NUMERO.findall(texto or ""))


def numeros_do_briefing(briefing: dict) -> set[str]:
    """Todo número que o narrador PODE escrever.

    Reúne o que o briefing entrega: ficha (ano, duração), share e percentual
    de cada grupo, n de reviews, menções e fração de cada tema. Qualquer
    número na prosa fora deste conjunto é invenção.
    """
    nums: set[str] = set()
    ficha = briefing.get("ficha") or {}
    for k in ("ano", "duracao_min"):
        if ficha.get(k):
            nums.add(str(ficha[k]))
    dist = briefing.get("distribuicao") or {}
    if dist.get("n_notas_total"):
        nums.add(str(dist["n_notas_total"]))
    if briefing.get("total_reviews_observadas"):
        nums.add(str(briefing["total_reviews_observadas"]))
    for g in (briefing.get("grupos") or {}).values():
        for k in ("n_reviews_analisadas", "share_pct"):
            if g.get(k) is not None:
                nums.add(str(g[k]))
        if g.get("rotulo_peso"):
            nums |= tokens_numericos(g["rotulo_peso"])
        for t in g.get("temas") or []:
            for k in ("mencoes", "de_n_reviews", "fracao_pct"):
                if t.get(k) is not None:
                    nums.add(str(t[k]))
    return nums


def numeros_inventados(texto: str, permitidos: set[str]) -> set[str]:
    return tokens_numericos(texto) - set(permitidos)


def rotulos_peso_faltando(texto: str, briefing: dict) -> list[str]:
    """Rótulos de peso que o briefing manda escrever e não estão no texto.

    Comparação literal — é o mesmo estatuto dos "trechos protegidos" de §E2:
    o rótulo COM o percentual é o que impede o peso de virar retórica solta.
    """
    faltando = []
    for nome in briefing.get("movimento3", {}).get("ordem", []):
        rot = (briefing.get("grupos", {}).get(nome) or {}).get("rotulo_peso")
        if rot and rot not in texto:
            faltando.append(rot)
    return faltando


def ordem_dos_grupos_ok(texto: str, briefing: dict) -> bool:
    """Os grupos aparecem no texto na ordem que o briefing fixou.

    Âncora: a primeira ocorrência do rótulo de peso de cada grupo. Grupo cujo
    rótulo não aparece é ignorado aqui — a ausência já é reportada por
    `rotulos_peso_faltando`, e contá-la duas vezes inflaria a contagem de
    flags sem acrescentar informação.
    """
    posicoes = []
    for nome in briefing.get("movimento3", {}).get("ordem", []):
        rot = (briefing.get("grupos", {}).get(nome) or {}).get("rotulo_peso")
        if rot and rot in texto:
            posicoes.append(texto.index(rot))
    return posicoes == sorted(posicoes)


def vocabulario_peso_violado(texto: str) -> bool:
    return bool(_PESO_PROIBIDO.search(texto or ""))


def verificar(texto: str, briefing: dict) -> dict:
    """Todas as checagens mecânicas de uma vez, no formato do relatório.

    `n_flags` conta só REPROVAÇÕES; `resenha_speak` é indicador e é
    reportado à parte, porque uma ocorrência não invalida a narrativa —
    misturar os dois esconderia qual dos dois tipos de problema o modelo tem.
    """
    inventados = numeros_inventados(texto, numeros_do_briefing(briefing))
    faltando = rotulos_peso_faltando(texto, briefing)
    ordem_ruim = not ordem_dos_grupos_ok(texto, briefing)
    formato = formato_invalido(texto)
    vocab = vocabulario_peso_violado(texto)
    speak = achar_resenha_speak(texto)
    return {
        "formato_invalido": formato,
        "numeros_inventados": sorted(inventados),
        "rotulos_faltando": faltando,
        "ordem_incorreta": ordem_ruim,
        "vocabulario_peso": vocab,
        "resenha_speak": speak,
        "n_resenha_speak": sum(a["n"] for a in speak),
        "n_flags": (int(formato) + int(bool(inventados)) + int(bool(faltando))
                    + int(ordem_ruim) + int(vocab)),
    }
