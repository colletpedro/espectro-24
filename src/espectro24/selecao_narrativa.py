"""[§D2, v1.9.9] Best-of-3 — N narrativas, UMA escolhida POR CÓDIGO.

**Por que gerar mais de uma.** A v1.7.3 já tinha registrado que a variância
entre chamadas do MESMO modelo com o MESMO prompt é grande o bastante para
decidir se uma edição é aceita ou descartada. A consequência natural é
gerar algumas e ficar com a melhor — desde que "melhor" seja definido por
algo que não seja outro LLM.

**Nenhum LLM julga prosa aqui.** Todo critério é contagem. Três deles são
medida direta de um defeito já observado (clichê da blocklist, repetição de
construção quantificadora, cobertura dos temas do briefing); o quarto,
o RITMO, é um PROXY DECLARADO — a hipótese é que texto com todas as frases
do mesmo comprimento lê como lista, e o desvio-padrão do comprimento mede
isso de longe. Proxy declarado significa: ele vale enquanto a calibração
contra leitura humana não o contradisser (`resultado/best-of-3/`).

**A ordem dos critérios é a da tarefa**, e a decisão de arredondar o ritmo a
palavras inteiras é o que impede que um float sem empates torne a cobertura
de temas decorativa.

**Fallback obrigatório.** Se nenhuma das N passar limpa, seleciona a de
MENOR SEVERIDADE e marca `precisa_retry` — o retry é DIRECIONADO às frases
infratoras, com o resto preservado literalmente. Descartar as N seria jogar
fora prosa boa por causa de uma frase.
"""
from __future__ import annotations

import re
import statistics
import unicodedata

from . import qualidade as q

# Fim de frase: ponto/!/? seguidos de espaço. Reticências e abreviação são
# ruído aceito — o número entra num desvio-padrão, não numa afirmação.
_FIM_FRASE = re.compile(r"(?<=[.!?])\s+")

# Palavras curtas e de ligação não identificam um tema; exigir que casem
# tornaria a cobertura uma medida de gramática.
_VAZIAS = {"de", "da", "do", "das", "dos", "e", "ou", "a", "o", "as", "os",
           "em", "no", "na", "um", "uma", "para", "com", "sem", "que", "por",
           "mais", "menos", "geral"}


def _normalizar(s: str) -> str:
    s = unicodedata.normalize("NFKD", (s or "").lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def frases(texto: str) -> list[str]:
    return [f.strip() for f in _FIM_FRASE.split(texto or "") if f.strip()]


def ritmo(texto: str) -> int:
    """Desvio-padrão do comprimento das frases, em PALAVRAS INTEIRAS.

    Arredondado de propósito: o valor é um proxy, e fingir resolução de
    casa decimal nele faria a cobertura de temas nunca desempatar nada.
    Menos de duas frases → 0 (não há dispersão a medir).
    """
    tamanhos = [len(f.split()) for f in frases(texto)]
    if len(tamanhos) < 2:
        return 0
    return round(statistics.pstdev(tamanhos))


def _termos_do_tema(tema: str) -> list[str]:
    return [p for p in re.findall(r"\w+", _normalizar(tema))
            if len(p) > 3 and p not in _VAZIAS]


def cobertura(texto: str, briefing: dict) -> float:
    """Fração dos temas do MOVIMENTO 3 que o texto realmente menciona.

    PROXY, e declarado como tal: um tema conta como coberto quando METADE
    ou mais dos seus termos de conteúdo aparecem no texto. Casamento
    semântico exato exigiria um segundo LLM julgando — que é justamente o
    que este módulo não faz.
    """
    alvo = _normalizar(texto)
    temas = [t.get("tema", "") for nome in briefing.get("movimento3", {}).get("ordem", [])
             for t in (briefing.get("grupos", {}).get(nome) or {}).get("temas") or []]
    temas = [t for t in temas if t]
    if not temas:
        return 1.0
    cobertos = 0
    for tema in temas:
        termos = _termos_do_tema(tema)
        if not termos:
            continue
        casados = sum(1 for termo in termos if termo in alvo)
        if casados * 2 >= len(termos):
            cobertos += 1
    return cobertos / len(temas)


def medir(texto: str, briefing: dict) -> dict:
    """Todas as métricas de um candidato, sem julgamento nenhum."""
    v = q.verificar(texto, briefing)
    # Sobre TODAS as construções usadas, não só as que estouraram o teto:
    # acima do teto a repetição já é flag (eliminatória), e um critério que
    # só existisse lá dentro nunca ordenaria os limpos entre si — que é
    # exatamente onde ele precisa decidir.
    rep = [a["n"] for a in q.construcoes_no_texto(texto, briefing)]
    return {
        "n_flags": v["n_flags"],
        "cliches": v["n_resenha_speak"],
        "repeticao_max": max(rep) if rep else 0,
        "ritmo": ritmo(texto),
        "cobertura": round(cobertura(texto, briefing), 3),
        "verificacao": v,
    }


def _chave(m: dict) -> tuple:
    """A ordem dos critérios da tarefa. Menor é melhor, então ritmo e
    cobertura entram NEGADOS (mais dispersão e mais cobertura são melhores)."""
    return (m["cliches"], m["repeticao_max"], -m["ritmo"], -m["cobertura"])


_NOMES_CRITERIO = ("cliche", "repeticao", "ritmo", "cobertura")


def _criterio_decisivo(vencedor: dict, resto: list[dict]) -> str:
    """Qual critério, na ordem, separou o vencedor de TODOS os demais.

    Sem isso a seleção é uma caixa-preta mecânica — auditável em princípio e
    opaca na prática.
    """
    if not resto:
        return "unico"
    a = _chave(vencedor)
    for i, nome in enumerate(_NOMES_CRITERIO):
        if all(a[i] < _chave(o)[i] for o in resto):
            return nome
    return "empate"


def selecionar(candidatos: list[str], briefing: dict) -> dict:
    """A escolha, e o registro de por que ela foi feita.

    `motivo`: `melhor_entre_limpos` (o caminho normal) ou `menor_severidade`
    (o fallback, que vem com `precisa_retry=True`). Empate total resolve
    pelo PRIMEIRO candidato — arbitrário, mas determinístico, que é o que
    importa para a comparação ser reproduzível.
    """
    medidos = []
    for i, texto in enumerate(candidatos):
        m = medir(texto, briefing)
        m["indice"] = i
        m["eliminado"] = m["n_flags"] > 0
        medidos.append(m)

    limpos = [m for m in medidos if not m["eliminado"]]
    pool = limpos or medidos
    if limpos:
        vencedor = min(pool, key=lambda m: (_chave(m), m["indice"]))
        motivo, precisa_retry = "melhor_entre_limpos", False
    else:
        # Fallback: severidade primeiro (menos flags), critérios depois.
        vencedor = min(pool, key=lambda m: (m["n_flags"], _chave(m), m["indice"]))
        motivo, precisa_retry = "menor_severidade", True

    resto = [m for m in pool if m["indice"] != vencedor["indice"]]
    return {
        "indice": vencedor["indice"],
        "narrativa": candidatos[vencedor["indice"]],
        "motivo": motivo,
        "precisa_retry": precisa_retry,
        "criterio_decisivo": _criterio_decisivo(vencedor, resto),
        "candidatos": [{k: m[k] for k in ("indice", "n_flags", "cliches",
                                          "repeticao_max", "ritmo",
                                          "cobertura", "eliminado")}
                       for m in medidos],
        "verificacao": vencedor["verificacao"],
    }


# ===========================================================================
# Retry DIRECIONADO — só as frases infratoras
# ===========================================================================

def frases_infratoras(texto: str, briefing: dict) -> list[dict]:
    """`[{frase, motivos}]` — as frases que violam algo, e o quê.

    O alvo do retry. Reescrever o texto inteiro perderia o que já estava
    bom e reintroduziria a variância que o best-of-3 existe para domar.
    """
    permitidos = q.numeros_do_briefing(briefing)
    faixas_ok = q.faixas_do_briefing(briefing)
    excedentes = {r["construcao"] for r in q.quantificadores_repetidos(texto, briefing)}
    blocklist = q.carregar_blocklist()

    saida = []
    for frase in frases(texto):
        motivos = []
        if q.numeros_inventados(frase, permitidos):
            motivos.append("numero_inventado")
        if any(a["expressao"] in _normalizar(frase) for a in
               q.achar_resenha_speak(frase, blocklist)):
            motivos.append("cliche")
        for a in q.construcoes_no_texto(frase, briefing):
            if faixas_ok and a["faixa"] not in faixas_ok:
                motivos.append("quantificador_fora_de_faixa")
            elif a["construcao"] in excedentes:
                motivos.append("construcao_repetida")
        if q.vocabulario_peso_violado(frase):
            motivos.append("vocabulario_peso")
        if motivos:
            saida.append({"frase": frase, "motivos": sorted(set(motivos))})
    return saida


_EXPLICACAO = {
    "numero_inventado": "contém número que não veio do briefing",
    "cliche": "usa expressão de resenha genérica",
    "construcao_repetida": "repete uma construção de frequência já usada "
                           "demais no texto; troque por outra do MESMO "
                           "conjunto (mesma faixa)",
    "quantificador_fora_de_faixa": "usa uma construção de frequência que "
                                   "afirma faixa diferente da medida",
    "vocabulario_peso": 'fala do peso como "das reviews"/"do público" em vez '
                        'de "das notas"',
}


def prompt_retry(texto: str, infratoras: list[dict]) -> str:
    """A mensagem do retry direcionado.

    Manda reescrever SÓ as frases listadas e devolver o texto inteiro com o
    resto LITERALMENTE intacto — mesma política de trecho protegido de §E2,
    aplicada ao complemento: aqui o protegido é tudo que não infringe.
    """
    L = ["O texto abaixo está quase certo. Reescreva APENAS as frases "
         "listadas depois dele, e devolva o texto COMPLETO com todo o "
         "restante preservado LITERALMENTE, palavra por palavra, na mesma "
         "ordem e nos mesmos parágrafos.", "", "TEXTO:", texto, "",
         "FRASES A CORRIGIR:"]
    for f in infratoras:
        L.append(f'  - "{f["frase"]}"')
        for m in f["motivos"]:
            L.append(f"      · {_EXPLICACAO.get(m, m)}")
    L += ["", "Não acrescente informação nova, não mude nenhum número e não "
          "altere a atribuição de nenhuma afirmação a nenhum grupo.", "",
          'Responda APENAS com JSON puro: {"narrativa": "<texto completo>"}']
    return "\n".join(L)
