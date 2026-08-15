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

from .config import MAX_PALAVRAS_PARAGRAFO, QUANT_MAX_REPETICOES

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


def _padrao_construcao(c: str) -> re.Pattern:
    """Regex de uma construção quantificadora, tolerante ao GÊNERO.

    O briefing entrega a forma masculina ("muitos", "poucos", "vários"), e o
    narrador escreve o que a frase pedir ("muitas notas", "várias"). Contar
    só a forma do briefing produziria falso negativo exatamente no defeito
    que esta checagem existe para pegar. A tolerância é estritamente de
    flexão final — nunca casa palavra diferente.
    """
    corpo = re.escape(_normalizar(c))
    corpo = re.sub(r"os\\b|os$", "(?:os|as)", corpo)
    corpo = re.sub(r"eles\\b|eles$", "(?:eles|elas)", corpo)
    return re.compile(rf"(?<!\w){corpo}(?!\w)")


def _texto_sem_rotulos_de_peso(texto: str, briefing: dict | None) -> str:
    """O texto com os `rotulo_peso` do briefing removidos.

    **Necessário, e o motivo é o desenho.** O rótulo de peso (§3[G])
    compartilha vocabulário com as construções quantificadoras ("a maioria",
    "boa parte") e é literal OBRIGATÓRIO — `rotulos_peso_faltando` reprova
    quem não o escreve. Contar suas ocorrências como repetição puniria o
    texto por obedecer exatamente ao que o briefing mandou.
    """
    if not briefing:
        return texto
    for g in (briefing.get("grupos") or {}).values():
        rot = g.get("rotulo_peso")
        if rot:
            texto = re.sub(re.escape(rot), " ", texto, flags=re.IGNORECASE)
    return texto


def construcoes_no_texto(texto: str, briefing: dict | None = None
                         ) -> list[dict]:
    """`[{construcao, faixa, n}]` de cada construção quantificadora usada.

    Faixa mais longa primeiro: sem isso, "a maioria" seria contada dentro de
    uma eventual construção maior que a contivesse. Os conjuntos são
    disjuntos e livres de substring cruzada por invariante testada
    (`briefing.FAIXAS_QUANTIFICADOR`), então a ordem só protege contra
    regressão futura.
    """
    from .briefing import FAIXAS_QUANTIFICADOR

    alvo = _normalizar(_texto_sem_rotulos_de_peso(texto or "", briefing))
    pares = [(c, faixa) for faixa, cs in FAIXAS_QUANTIFICADOR.items()
             for c in cs]
    pares.sort(key=lambda par: -len(par[0]))
    achados, consumido = [], alvo
    for c, faixa in pares:
        n = len(_padrao_construcao(c).findall(consumido))
        if n:
            achados.append({"construcao": c, "faixa": faixa, "n": n})
            consumido = _padrao_construcao(c).sub(" ", consumido)
    return achados


def faixas_do_briefing(briefing: dict) -> set[str]:
    """As faixas que o briefing REALMENTE atribuiu a algum tema."""
    faixas = set()
    for g in (briefing.get("grupos") or {}).values():
        for t in g.get("temas") or []:
            if t.get("faixa"):
                faixas.add(t["faixa"])
    return faixas


def quantificadores_fora_de_faixa(texto: str, briefing: dict) -> list[str]:
    """Construções cuja FAIXA o briefing não atribuiu a tema nenhum.

    [v1.9.9] Substitui a comparação com a string literal por comparação de
    PERTENCIMENTO — que é o que a invariante sempre quis dizer. O código
    continua sendo a autoridade sobre a faixa; o narrador escolhe a palavra
    dentro dela. Uma construção de faixa não atribuída afirma uma
    frequência que ninguém mediu.

    Sem faixa nenhuma no briefing (grupo em `sem_quantificador`, §3[C3]) a
    checagem se cala: não há o que violar.
    """
    permitidas = faixas_do_briefing(briefing)
    if not permitidas:
        return []
    return sorted({a["construcao"] for a in construcoes_no_texto(texto, briefing)
                   if a["faixa"] not in permitidas})


def quantificadores_repetidos(texto: str, briefing: dict | None = None,
                              maximo: int = QUANT_MAX_REPETICOES
                              ) -> list[dict]:
    """Construções usadas mais de `maximo` vezes — o TIQUE, medido.

    A razão de esta checagem não existir antes é que a repetição não violava
    regra nenhuma: o briefing entregava a faixa como string única e mandava
    escrevê-la em cada tema. O texto obedecia.
    """
    return [{"construcao": a["construcao"], "n": a["n"]}
            for a in construcoes_no_texto(texto, briefing) if a["n"] > maximo]


def _paragrafos(texto: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n+", texto or "") if p.strip()]


def _min_paragrafos(briefing: dict) -> int:
    """O mínimo é o número de movimentos com orçamento maior que zero.

    Deliberadamente NÃO é constante: sem ficha o movimento 1 não existe
    (`ORCAMENTO_SEM_FICHA`), e um mínimo fixo de 3 reprovaria o narrador por
    obedecer à instrução de pulá-lo.
    """
    orc = briefing.get("orcamento_frases")
    if orc is None:
        return 3 if briefing.get("ficha") else 2
    return sum(1 for mov in ("movimento1", "movimento2", "movimento3")
               if (orc.get(mov) or (0, 0))[1] > 0)


def problemas_de_paragrafo(texto: str, briefing: dict) -> dict:
    """Estrutura de parágrafo: `{n_paragrafos, minimo, insuficientes, longos}`.

    [v1.9.9] `gemini-3.1-pro` entregou os 3 filmes num bloco único de até
    318 palavras e NENHUMA flag disparou — `formato_invalido` (v1.7.2) checa
    se a prosa veio embrulhada em JSON ou markdown, não se ela é legível.
    """
    ps = _paragrafos(texto)
    minimo = _min_paragrafos(briefing)
    longos = [{"indice": i, "n_palavras": len(p.split())}
              for i, p in enumerate(ps) if len(p.split()) > MAX_PALAVRAS_PARAGRAFO]
    return {"n_paragrafos": len(ps), "minimo": minimo,
            "insuficientes": len(ps) < minimo, "longos": longos}


def paragrafos_por_grupo(texto: str, briefing: dict) -> dict[str, int | None]:
    """Índice (0-based) do parágrafo em que o `rotulo_peso` de cada grupo
    do MOVIMENTO 3 aparece pela primeira vez — `None` se o rótulo não
    aparecer (já reprovado à parte por `rotulos_peso_faltando`).

    Mesma âncora literal usada por `ordem_dos_grupos_ok`, aplicada a
    parágrafo em vez de posição bruta de caractere.
    """
    ps = _paragrafos(texto)
    limites, cursor = [], 0
    for p in ps:
        pos = texto.find(p, cursor)
        limites.append((pos, pos + len(p)) if pos != -1 else (-1, -1))
        cursor = limites[-1][1] if pos != -1 else cursor

    resultado: dict[str, int | None] = {}
    for nome in briefing.get("movimento3", {}).get("ordem", []):
        rot = (briefing.get("grupos", {}).get(nome) or {}).get("rotulo_peso")
        idx_char = texto.find(rot) if rot else -1
        if idx_char == -1:
            resultado[nome] = None
            continue
        resultado[nome] = next(
            (i for i, (ini, fim) in enumerate(limites) if ini <= idx_char <= fim),
            None)
    return resultado


def grupos_sem_paragrafo_proprio(texto: str, briefing: dict) -> list[str]:
    """Grupos APRESENTADOS (permissão de citar tema — fora de
    `sem_analise`) que dividem parágrafo com outro grupo apresentado.

    [v1.9.9] Medido: `cidade-de-deus` saiu com 3 parágrafos no total —
    passa em `problemas_de_paragrafo` — mas o MOVIMENTO 3 inteiro, os 3
    grupos, ficou espremido num bloco único. `problemas_de_paragrafo` só
    conta o total de parágrafos do texto; esta checagem confere que cada
    grupo apresentado tem o SEU. Um grupo em `sem_analise` não entra na
    contagem — a regra acompanha o número real de grupos apresentados, não
    um total fixo de 3.
    """
    apresentados = [
        nome for nome in briefing.get("movimento3", {}).get("ordem", [])
        if (briefing.get("grupos", {}).get(nome) or {})
           .get("permissoes", {}).get("pode_citar_temas")]
    pares = paragrafos_por_grupo(texto, briefing)
    vistos: dict[int, str] = {}
    colisoes = []
    for nome in apresentados:
        idx = pares.get(nome)
        if idx is None:
            continue
        if idx in vistos:
            colisoes.append(nome)
        else:
            vistos[idx] = nome
    return colisoes


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
    fora_faixa = quantificadores_fora_de_faixa(texto, briefing)
    repetidos = quantificadores_repetidos(texto, briefing)
    par = problemas_de_paragrafo(texto, briefing)
    sem_paragrafo_proprio = grupos_sem_paragrafo_proprio(texto, briefing)
    return {
        "quantificador_fora_de_faixa": fora_faixa,
        "quantificador_repetido": repetidos,
        "paragrafos": par,
        "n_paragrafos": par["n_paragrafos"],
        "paragrafos_insuficientes": par["insuficientes"],
        "paragrafos_longos": par["longos"],
        "grupos_sem_paragrafo_proprio": sem_paragrafo_proprio,
        "formato_invalido": formato,
        "numeros_inventados": sorted(inventados),
        "rotulos_faltando": faltando,
        "ordem_incorreta": ordem_ruim,
        "vocabulario_peso": vocab,
        "resenha_speak": speak,
        "n_resenha_speak": sum(a["n"] for a in speak),
        "n_flags": (int(formato) + int(bool(inventados)) + int(bool(faltando))
                    + int(ordem_ruim) + int(vocab)
                    + int(bool(fora_faixa)) + int(bool(repetidos))
                    + int(par["insuficientes"]) + int(bool(par["longos"]))
                    + int(bool(sem_paragrafo_proprio))),
    }
