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


def spans_por_grupo(texto: str, briefing: dict) -> dict[str, str]:
    """O trecho de `texto` atribuído a cada grupo do MOVIMENTO 3.

    Mesma âncora que `qualidade.ordem_dos_grupos_ok` já usa para checar
    ordem: a primeira ocorrência LITERAL do `rotulo_peso` do grupo. De onde
    o grupo começa até onde o PRÓXIMO grupo ancorado começa (ou o fim do
    texto). Grupo cujo rótulo não aparece tem span vazio — a ausência já é
    reprovada à parte por `qualidade.rotulos_peso_faltando`; aqui ela só
    significa "nada a contar para este grupo".
    """
    ordem = briefing.get("movimento3", {}).get("ordem", [])
    grupos = briefing.get("grupos", {})
    achados = []
    for nome in ordem:
        rot = (grupos.get(nome) or {}).get("rotulo_peso")
        pos = texto.find(rot) if rot else -1
        if pos != -1:
            achados.append((pos, nome))
    achados.sort()
    spans = {nome: "" for nome in ordem}
    for i, (pos, nome) in enumerate(achados):
        fim = achados[i + 1][0] if i + 1 < len(achados) else len(texto)
        spans[nome] = texto[pos:fim]
    return spans


# Conectivos que introduzem uma afirmação nova dentro do MESMO período —
# "muitos apontam X, ENQUANTO vários valorizam Y" são dois pontos, não um.
# Lista pequena e literal de propósito: um conectivo perdido subconta (o que
# só torna a checagem mais conservadora); um conectivo comum tratado como
# separador por engano superconta, que é o erro que importa evitar aqui.
_CONECTIVOS_CLAUSULA = ("ao passo que", "enquanto", "além disso",
                        "por sua vez", "embora")
_QUEBRA_CLAUSULA = re.compile(
    r"[.;!?]+|,(?=\s)|(?:%s)" % "|".join(re.escape(c) for c in _CONECTIVOS_CLAUSULA),
    re.IGNORECASE)


def _clausulas(span: str) -> list[str]:
    """Fragmentos do `span` com pelo menos 4 palavras — proxy de "afirmação
    distinta", sem exigir identificar QUAL afirmação é. Fragmentos curtos
    ("Nesse segmento", "e vários") são resíduo de pontuação, não conteúdo."""
    return [p.strip() for p in _QUEBRA_CLAUSULA.split(span) if len(p.split()) >= 4]


def cobertura(texto: str, briefing: dict) -> float:
    """Fração dos temas do MOVIMENTO 3 cobertos — por ESTRUTURA, não léxico.

    [v1.9.9, Entrega 1 da sessão de fechamento] Substitui o casamento de
    termos de conteúdo com o RÓTULO do tema, que tinha falso negativo
    SISTEMÁTICO em paráfrase — medido na calibração: em `cure`, 5 dos 9
    temas "ausentes" do candidato escolhido estavam no texto, só reescritos
    sem sobreposição lexical ("Pacing Lento e Deliberado" → "o andamento
    metódico"); a cobertura real era 1,00, a medida 0,44. O proxy antigo
    punia exatamente o texto que evita copiar o rótulo — a prosa melhor.

    A pergunta muda de "este tema específico foi mencionado" (exige
    semântica — casamento por SIGNIFICADO, que só um segundo LLM faz) para
    algo mais fraco e puramente ESTRUTURAL: "o span do GRUPO CERTO (ancorado
    pelo `rotulo_peso` literal, `spans_por_grupo`) tem tantas afirmações
    distintas quanto o briefing atribuiu a ele, na ORDEM em que os grupos
    aparecem?" GRUPO é garantido pelo span; ORDEM, por `spans_por_grupo`
    percorrer os grupos na ordem do briefing e nunca misturar conteúdo de
    um grupo no span de outro.

    A primeira cláusula de cada span é descartada da contagem: é tipicamente
    a frase de abertura que retoma o rótulo de peso ("a grande maioria das
    notas... concentra as avaliações mais favoráveis") e não corresponde a
    um tema específico — contá-la infla a cobertura de qualquer grupo com
    ao menos uma frase escrita.

    **O que isto DECLARADAMENTE não verifica:** que a cláusula N seja
    REALMENTE sobre o tema N — só que existem cláusulas suficientes. Uma
    mesma ideia repetida três vezes com sinônimos conta como três. É uma
    troca deliberada, no mesmo espírito de todo proxy deste módulo: extinguir
    o falso negativo sistemático (grave e medido) custa a capacidade de
    pegar a omissão de UM tema específico dentro de um grupo bem escrito em
    volume (mais rara, e sem exemplo medido até agora).

    Grupo sem span (rótulo ausente do texto) conta 0 cláusulas — não herda
    nem empresta cobertura de outro grupo.
    """
    spans = spans_por_grupo(texto, briefing)
    total_temas = total_cobertos = 0
    for nome, span in spans.items():
        n_temas = len((briefing.get("grupos", {}).get(nome) or {}).get("temas") or [])
        if not n_temas:
            continue
        total_temas += n_temas
        clausulas = _clausulas(span)
        corpo = clausulas[1:] if len(clausulas) > 1 else clausulas
        total_cobertos += min(len(corpo), n_temas)
    return total_cobertos / total_temas if total_temas else 1.0


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
