"""[§D2, v1.9.8] Briefing DETERMINÍSTICO — o código decide, o narrador verbaliza.

Até a v1.9.7 o narrador fazia duas coisas ao mesmo tempo: **selecionar** o
que dizer (quais temas, em que ordem, com que ênfase) e **escrever**,
segurando ~18 invariantes de instrução simultaneamente. Este módulo separa
as duas: `montar_briefing` produz, em CÓDIGO, um documento com todas as
decisões já tomadas; `PROMPT_NARRADOR_BRIEFING` é um prompt que só pede
prosa.

É a terceira aplicação do padrão de §3[D] ("instrução não remove o que a
distribuição do material impõe — a saída é arquitetura"): v1.2.3 moveu o
rótulo de quantificador para o código depois de a calibração por instrução
reincidir; v1.6.0 separou narrador e editor em dois estágios depois de
empilhar honestidade e fluência num prompt só falhar. Aqui o mesmo
princípio chega ao que o narrador ESCOLHE.

**A fronteira, e ela é o ponto:** nem toda invariante é computável. As que
podem ser resolvidas por código migram para dado (`INVARIANTES_MIGRADAS`);
as que são regras sobre COMO escrever uma frase — anti-spoiler, proibição
de fato externo, tom neutro, respeito à minoria, vocabulário
"notas"/"reviews" — continuam no prompt (`INVARIANTES_REMANESCENTES`),
porque o código não tem como pré-decidir isso sem escrever a frase ele
mesmo. A medida de sucesso é quantas SAÍRAM, não zero.

**O que o narrador continua NÃO podendo fazer:** escolher tema, computar
número, decidir ordem. Mesma autoridade do código sobre número que vale
desde a v1.1.1 (denominador) e a v1.2.3 (quantificador).
"""
from __future__ import annotations

from .buckets import FRONTEIRAS
from .config import PISO_ESCALONADO, QUANT_MAX_REPETICOES

# Ordem canônica dos buckets — usada como desempate estável e como ordem de
# fallback quando não há distribuição. Sem ela, dois filmes com o mesmo
# perfil poderiam sair em ordens diferentes por acidente de iteração.
ORDEM_CANONICA = tuple(FRONTEIRAS)

# Quantos temas de cada grupo o MOVIMENTO 3 usa. Era a instrução "priorize
# os 2-3 temas MAIS FORTES de cada grupo, não a cobertura completa dos 6
# possíveis" — vira corte em código, com o resto reportado em
# `temas_omitidos` para que o truncamento não seja silencioso.
MAX_TEMAS_POR_GRUPO = 3

# O `estado_piso` (§3[C3]) traduzido em PERMISSÃO. Era o narrador que tinha
# de inferir, de `modo=sem_analise`, o que podia dizer sobre um grupo mal
# medido. Agora é dado explícito, e a ausência de permissão vem junto com a
# ausência do campo correspondente (ver `_temas_do_grupo`): o que não pode
# ser citado não chega ao narrador para ser copiado por engano.
PERMISSOES_POR_ESTADO = {
    "completa": {"pode_citar_temas": True, "pode_citar_numero": True,
                 "pode_citar_quantificador": True},
    "sem_quantificador": {"pode_citar_temas": True, "pode_citar_numero": True,
                          "pode_citar_quantificador": False},
    "sem_numero": {"pode_citar_temas": True, "pode_citar_numero": False,
                   "pode_citar_quantificador": False},
    "sem_analise": {"pode_citar_temas": False, "pode_citar_numero": False,
                    "pode_citar_quantificador": False},
}

# Orçamento de frases por movimento. Era instrução em prosa ("2-3 frases",
# "3-5 frases", "enxuto"). O movimento 1 é (0,0) sem ficha — o que
# substitui a condicional "SÓ escreva este movimento SE houver FICHA".
ORCAMENTO_COM_FICHA = {"movimento1": (2, 3), "movimento2": (0, 5),
                       "movimento3": (4, 8)}
ORCAMENTO_SEM_FICHA = {"movimento1": (0, 0), "movimento2": (0, 5),
                       "movimento3": (4, 8)}

# --- A contagem que a Entrega 1 reporta -----------------------------------
# Cada item é uma invariante que existia como INSTRUÇÃO VIVA no prompt da
# v1.9.7 (`_NARRADOR_PARTE_1` + regra (c) + `_NARRADOR_PARTE_2`). Ficam aqui
# como dado, não como prosa, para que o número seja verificável e não uma
# afirmação do relatório.
INVARIANTES_MIGRADAS = (
    "ordem do MOVIMENTO 3 (abre pelo grupo de maior peso)",
    "seleção dos 2-3 temas mais fortes por grupo",
    "quantificador verbal de cada tema (escala de força)",
    "rótulo de peso de cada grupo (a partir do share real)",
    "marcação de perspectiva exigida por grupo",
    "condicional do MOVIMENTO 1 (só existe se houver ficha)",
    "orçamento de frases de cada movimento",
    "o que pode ser dito de um grupo conforme o estado do piso",
    "ênfase proporcional ao peso de cada grupo",
    "denominador de cada frequência de tema",
)
INVARIANTES_REMANESCENTES = (
    "anti-spoiler em qualquer movimento",
    "proibição de importar fato externo (fidelidade à ficha e aos temas)",
    "tom NEUTRO e sem valência no MOVIMENTO 2",
    "critério de categoria do MOVIMENTO 2 (descritivo, nunca qualidade)",
    "respeito à minoria (menos espaço, mesma seriedade)",
    'vocabulário "das notas", nunca "das reviews"/"do público"',
    "proibição de número-síntese (nota média, score)",
    "papel do leitor (quem ainda não assistiu)",
    "forma (pt-BR, sem aspas, sem subtítulos)",
)


def extrair_narrativa(bruto: str) -> str:
    """A narrativa da resposta do narrador, tolerante a escape inconsistente.

    **Defeito real que motiva** (medido em `cidade-de-deus`, 2026-08-15):
    o DeepSeek devolve prosa de vários parágrafos e escapa a quebra de linha
    de forma INCONSISTENTE dentro da mesma resposta — parte como `\\n`
    (válido) e parte como newline cru (JSON inválido). `json.loads` recusa a
    resposta inteira, e o texto, que está perfeitamente bom, se perde.

    A estratégia é escalonada, do mais estrito ao mais tolerante:
      1. JSON estrito — o caminho normal, e o único que valida a estrutura;
      2. JSON com as quebras de linha CRUAS escapadas — conserta o defeito
         observado sem afrouxar mais nada;
      3. extração direta do campo `narrativa` por regex — último recurso,
         possível aqui só porque o schema deste estágio é UM campo de texto
         (não vale para a síntese §D, cujo JSON tem estrutura aninhada).

    Devolve `""` quando nada funciona — o chamador trata como falha, em vez
    de receber prosa meio parseada e não perceber.
    """
    import json as _json
    import re as _re

    t = (bruto or "").strip()
    if not t:
        return ""
    # remove cerca de código, se vier
    if t.startswith("```"):
        t = _re.sub(r"^```[a-z]*\s*|\s*```$", "", t, flags=_re.IGNORECASE)

    try:
        return (_json.loads(t) or {}).get("narrativa", "") or ""
    except Exception:  # noqa: BLE001
        pass

    # (2) escapa newline/tab CRUS que estejam dentro de uma string JSON.
    dentro, saida, i = False, [], 0
    while i < len(t):
        c = t[i]
        if c == "\\" and i + 1 < len(t):
            saida.append(t[i:i + 2]); i += 2; continue
        if c == '"':
            dentro = not dentro
        if dentro and c == "\n":
            saida.append("\\n")
        elif dentro and c == "\t":
            saida.append("\\t")
        else:
            saida.append(c)
        i += 1
    try:
        return (_json.loads("".join(saida)) or {}).get("narrativa", "") or ""
    except Exception:  # noqa: BLE001
        pass

    # (3) o campo, por regex — schema de UM campo torna isso seguro aqui.
    m = _re.search(r'"narrativa"\s*:\s*"(.*)"\s*}\s*$', t, _re.DOTALL)
    if not m:
        return ""
    bruto_campo = m.group(1)
    return (bruto_campo.replace("\\n", "\n").replace('\\"', '"')
            .replace("\\\\", "\\").strip())


def _estado_piso(bucket: dict) -> str:
    """`estado_piso` do bucket, DERIVADO de `n_validas` quando ausente.

    O campo é da v1.9.0 e não está serializado em `resultado/*.json`
    publicado antes dela — e um default para `"sem_analise"` seria o pior
    fallback possível: apagaria em silêncio temas perfeitamente bons (medido
    ao vivo em `cure`, 50 reviews com 6 temas indo para "SEM TEMAS"). Como o
    estado é FUNÇÃO de `n_validas` pela mesma tabela que o pipeline usa
    (`PISO_ESCALONADO`, §3[C3]), recomputá-lo é exato, não uma estimativa.
    """
    declarado = bucket.get("estado_piso")
    if declarado:
        return declarado
    n = bucket.get("n_validas", 0) or 0
    for limiar, estado in PISO_ESCALONADO:
        if n >= limiar:
            return estado
    return "sem_analise"


def _fracao_pct(mencoes: int, n: int) -> int:
    return round(100 * mencoes / n) if n else 0


# [v1.9.9] CONSTRUÇÕES POR FAIXA — a faixa é do código, a palavra é do
# narrador.
#
# Defeito medido na leitura humana da v1.9.8: em `cure`, os QUATRO modelos
# escrevem "muitos" 8 vezes no mesmo texto. A causa não é o modelo — o
# briefing entregava a faixa como STRING ÚNICA ("escreva a frequência
# assim: muitos"), tema a tema, e o modelo obedecia literalmente. A
# repetição era o comportamento correto diante de um briefing que mandava
# repetir.
#
# A fronteira que isto preserva: a FAIXA é afirmação sobre o dado (fica no
# código, calibração intocada desde a v1.2.3); a CONSTRUÇÃO é escolha de
# palavra (vai para quem escreve as palavras).
#
# **Invariante crítica:** os conjuntos são DISJUNTOS e nenhuma construção é
# substring de uma construção de outra faixa — se fossem sobrepostos, a
# checagem de pertencimento (`qualidade.quantificadores_fora_de_faixa`) não
# decidiria nada e a faixa deixaria de ser verdade sobre o dado. Há teste
# para as duas coisas. A construção CANÔNICA (a da v1.2.3) abre cada lista,
# para que o valor histórico continue exprimível.
FAIXAS_QUANTIFICADOR: dict[str, tuple[str, ...]] = {
    "poucos": ("poucos", "uma minoria", "um pequeno número", "raros"),
    "alguns": ("alguns", "uma parte", "parte deles"),
    "muitos": ("muitos", "boa parte", "uma parcela expressiva", "vários",
               "um número considerável"),
    "cerca de metade": ("cerca de metade", "aproximadamente metade",
                        "perto da metade", "metade deles"),
    "a maioria": ("a maioria", "a maior parte", "a maior parcela"),
    "quase todos": ("quase todos", "praticamente todos", "a quase totalidade"),
}


def faixa_quantificador(pct: int) -> str:
    """A faixa de `pct` — mesma escala e mesma resolução de empate da
    v1.2.3. Nome público porque a faixa passou a ser DADO do briefing (é
    ela que a verificação mecânica consulta), não mais um detalhe interno
    que só existia para virar string."""
    return _quantificador(pct)


def _quantificador(pct: int) -> str:
    """Mesma escala e mesma resolução de empate da v1.2.3 (`synthesize.
    _rotulo_quantificador`) — reimportada por valor, não por import, para
    que este módulo não dependa de `synthesize` (que importa SDKs)."""
    for rotulo, lo, hi, hi_incl in (
        ("poucos", 0, 10, False), ("alguns", 10, 25, True),
        ("muitos", 25, 50, True), ("cerca de metade", 40, 60, True),
        ("a maioria", 50, 80, True), ("quase todos", 80, 100, True),
    ):
        if pct >= lo and (pct <= hi if hi_incl else pct < hi):
            return rotulo
    return "poucos"


def _rotulo_peso(pct: int) -> str:
    for rotulo, lo in (("a grande maioria", 70), ("a maioria", 50),
                       ("boa parte", 30), ("uma parcela", 15),
                       ("uma fração mínima", 0)):
        if pct >= lo:
            return rotulo
    return "uma fração mínima"


def _rotulo_peso_completo(pct: int) -> str:
    return f"{_rotulo_peso(pct)} das notas (~{pct}%)"


def _marcacao_perspectiva(pct: int, dominante: int | None) -> str:
    """Mesmos limiares da v1.5.0 — o grupo dominante não exige marcador
    extra (o rótulo de peso já ancora); quanto menor o grupo diante do
    dominante, mais cedo o marcador precisa aparecer."""
    if not dominante:
        return "nenhuma"
    if pct >= dominante:
        return "nenhuma"
    return "antecipada" if pct * 2 < dominante else "simples"


def _shares(output: dict) -> dict[str, int]:
    dist = output.get("distribuicao") or {}
    por_bucket = dist.get("por_bucket") or {}
    return {n: int(v) for n, v in por_bucket.items() if v is not None}


def _temas_do_grupo(bucket: dict, permissoes: dict,
                    max_temas: int) -> tuple[list[dict], int]:
    """Temas ordenados, cortados e já com quantificador — ou vazio quando o
    piso não permite citar tema nenhum.

    Um campo que a permissão nega NÃO é incluído: deixá-lo no briefing
    marcado como proibido convidaria a cópia por engano.
    """
    if not permissoes["pode_citar_temas"]:
        return [], 0
    brutos = list(bucket.get("temas") or [])
    brutos.sort(key=lambda t: -(t.get("mencoes_aproximadas") or 0))
    usados, omitidos = brutos[:max_temas], max(0, len(brutos) - max_temas)
    saida = []
    for t in usados:
        pct = _fracao_pct(t.get("mencoes_aproximadas") or 0,
                          t.get("n_reviews_analisadas") or 0)
        item = {"tema": t.get("tema"), "fracao_pct": pct,
                "exemplo": t.get("exemplo_parafraseado")}
        if permissoes["pode_citar_numero"]:
            item["mencoes"] = t.get("mencoes_aproximadas")
            item["de_n_reviews"] = t.get("n_reviews_analisadas")
        if permissoes["pode_citar_quantificador"]:
            faixa = _quantificador(pct)
            item["faixa"] = faixa
            item["quantificadores"] = list(FAIXAS_QUANTIFICADOR[faixa])
            # a canônica continua exposta: é o valor que a v1.2.3 publicava
            # e o que a telemetria histórica compara.
            item["quantificador"] = faixa
        saida.append(item)
    return saida, omitidos


def _material_movimento2(output: dict) -> list[dict]:
    """TODOS os temas de TODOS os grupos, sem número e sem quantificador.

    **Por que existir separado (diagnóstico da Entrega 3, v1.9.9).** O
    movimento 2 encolheu em todos os modelos — em `gemini-3.7-flash`/`cure`,
    para UMA frase. A causa não é o orçamento `(0,5)`, que nenhum modelo
    encostou, nem o prompt, cuja regra o modelo estava obedecendo: é a
    TRUNCAGEM. O único material do movimento 2 era a lista de temas, e ela
    chegava cortada em `MAX_TEMAS_POR_GRUPO = 3` — corte definido para o
    movimento 3. O movimento 2 precisa de propriedade DESCRITIVA presente em
    mais de um grupo, e é nos postos médios que ela mora: em `cure`, dentro
    do top-3 só o RITMO é comum aos três grupos (uma propriedade → a regra
    de uma frase dispara), enquanto ATMOSFERA (`medianas` #4, `positivas`
    #1) e AMBIGUIDADE DO FINAL (`medianas` #2, `positivas` #6) caem no corte.

    Sem número e sem quantificador de propósito: frequência aqui seria
    convite a escrever contagem fora do movimento 3, que é o único lugar
    onde ela é atribuída a um grupo. E respeita a mesma permissão de piso —
    grupo que não pode citar tema não entrega tema aqui tampouco.
    """
    material: list[dict] = []
    for b in output.get("buckets", []):
        nome = b.get("bucket")
        if not nome:
            continue
        permissoes = PERMISSOES_POR_ESTADO.get(
            _estado_piso(b), PERMISSOES_POR_ESTADO["sem_analise"])
        if not permissoes["pode_citar_temas"]:
            continue
        brutos = sorted(b.get("temas") or [],
                        key=lambda t: -(t.get("mencoes_aproximadas") or 0))
        for t in brutos:
            if t.get("tema"):
                material.append({"tema": t["tema"], "grupo": nome})
    return material


def montar_briefing(output: dict, max_temas_por_grupo: int = MAX_TEMAS_POR_GRUPO
                    ) -> dict:
    """O documento de decisões, pronto para virar prosa.

    Não lê nada além de `output` (o dict já validado de `build_output`) —
    mesma fronteira de §D2 desde a v1.2.0: **nunca reviews brutas**. O que
    não estiver aqui não chega ao narrador.
    """
    shares = _shares(output)
    dominante = max(shares.values()) if shares else None

    grupos: dict[str, dict] = {}
    for b in output.get("buckets", []):
        nome = b.get("bucket")
        if not nome:
            continue
        estado = _estado_piso(b)
        permissoes = dict(PERMISSOES_POR_ESTADO.get(
            estado, PERMISSOES_POR_ESTADO["sem_analise"]))
        temas, omitidos = _temas_do_grupo(b, permissoes, max_temas_por_grupo)
        g = {
            "n_reviews_analisadas": b.get("n_validas", 0),
            "estado_piso": estado,
            "permissoes": permissoes,
            "observacao_geral": b.get("observacao_geral", ""),
            "temas": temas,
            "temas_omitidos": omitidos,
        }
        if nome in shares:
            pct = shares[nome]
            g["share_pct"] = pct
            g["rotulo_peso"] = _rotulo_peso_completo(pct)
            g["marcacao_perspectiva"] = _marcacao_perspectiva(pct, dominante)
        else:
            g["marcacao_perspectiva"] = "nenhuma"
        grupos[nome] = g

    # Ordem do MOVIMENTO 3: maior peso primeiro, desempate pela ordem
    # canônica. Era instrução; vira lista.
    presentes = [n for n in ORDEM_CANONICA if n in grupos]
    presentes += [n for n in grupos if n not in ORDEM_CANONICA]
    ordem = sorted(presentes,
                   key=lambda n: (-shares.get(n, -1), ORDEM_CANONICA.index(n)
                                  if n in ORDEM_CANONICA else 99))

    ficha = output.get("ficha")
    orcamento = dict(ORCAMENTO_COM_FICHA if ficha else ORCAMENTO_SEM_FICHA)

    return {
        "ficha": ficha,
        "total_reviews_observadas": output.get("total_reviews_observadas", 0),
        "distribuicao": {
            "disponivel": bool(shares),
            "n_notas_total": (output.get("distribuicao") or {}).get(
                "n_notas_total", 0),
        },
        "grupos": grupos,
        "movimento2": {"material": _material_movimento2(output)},
        "movimento3": {"ordem": ordem},
        "orcamento_frases": orcamento,
    }


def serializar_briefing(b: dict) -> str:
    """O briefing como texto, para entrar na mensagem do usuário.

    Estrutura explícita e determinística: mesma entrada → mesma saída, byte
    a byte (é o que permite o cache de prefixo e o A/B entre providers).
    """
    L: list[str] = ["BRIEFING (todas as decisões já foram tomadas pelo "
                    "código — verbalize, não escolha):", ""]

    o = b["orcamento_frases"]
    L.append("ORÇAMENTO DE FRASES:")
    for mov in ("movimento1", "movimento2", "movimento3"):
        lo, hi = o[mov]
        L.append(f"  {mov}: {lo} a {hi} frases"
                 + ("  (NÃO escreva este movimento)" if hi == 0 else ""))
    L.append("")
    L.append("SOBRE AS FREQUÊNCIAS: cada tema abaixo vem com um CONJUNTO de "
             "construções equivalentes — todas dizem a mesma faixa, e "
             "qualquer uma delas é correta. Escolha uma e VARIE entre os "
             f"temas: não repita a mesma construção mais de "
             f"{QUANT_MAX_REPETICOES} vezes no texto inteiro. É PROIBIDO "
             "usar uma construção que não esteja no conjunto do tema — "
             "ela diria uma faixa diferente da medida.")
    L.append("")

    ficha = b.get("ficha")
    if ficha:
        L.append("FICHA (fonte EXCLUSIVA do movimento 1):")
        for k in ("titulo", "ano", "diretor", "duracao_min"):
            L.append(f"  {k}: {ficha.get(k)}")
        L.append(f"  generos: {', '.join(ficha.get('generos') or [])}")
        L.append(f"  sinopse_oficial: {ficha.get('sinopse_oficial')}")
        L.append("")

    material = (b.get("movimento2") or {}).get("material") or []
    if material:
        L.append("MATERIAL DO MOVIMENTO 2 (todos os temas de todos os "
                 "grupos, SEM frequência):")
        for m in material:
            L.append(f"    - [{m['grupo']}] {m['tema']}")
        L.append("  Use esta lista SÓ para localizar propriedade DESCRITIVA "
                 "que apareça em mais de um grupo com o mesmo núcleo "
                 "factual. É PROIBIDO citar frequência aqui e é PROIBIDO "
                 "usar esta lista para acrescentar tema ao movimento 3 — o "
                 "movimento 3 usa apenas os temas listados por grupo abaixo.")
        L.append("")

    L.append("ORDEM OBRIGATÓRIA DO MOVIMENTO 3 (nesta sequência): "
             + " → ".join(b["movimento3"]["ordem"]))
    L.append("")

    rotulo = {"negativas": "quem não gostou", "medianas": "quem ficou no meio",
              "positivas": "quem gostou"}
    for nome in b["movimento3"]["ordem"]:
        g = b["grupos"][nome]
        cab = f"GRUPO {nome.upper()} ({rotulo.get(nome, nome)}) — " \
              f"{g['n_reviews_analisadas']} reviews analisadas"
        if "rotulo_peso" in g:
            cab += f' · escreva o peso assim: "{g["rotulo_peso"]}"'
        L.append(cab + ":")
        L.append(f"  marcacao_perspectiva exigida: {g['marcacao_perspectiva']}")
        p = g["permissoes"]
        if not p["pode_citar_temas"]:
            L.append("  SEM TEMAS — material insuficiente. Diga apenas que "
                     "este grupo tem poucas reviews para análise temática; "
                     "NÃO invente tema, número ou quantificador.")
        else:
            if g["observacao_geral"]:
                L.append(f"  observação: {g['observacao_geral']}")
            L.append("  temas (use estes, nesta ordem; não acrescente outros):")
            for t in g["temas"]:
                linha = f"    - {t['tema']}"
                if "quantificadores" in t:
                    # [v1.9.9] o conjunto, não a ordem literal — ver
                    # FAIXAS_QUANTIFICADOR. Mandar a string única produziu 8
                    # "muitos" no mesmo texto, nos 4 modelos medidos.
                    opcoes = " | ".join(t["quantificadores"])
                    linha += f" · frequência (escolha UMA destas): {opcoes}"
                if "mencoes" in t:
                    linha += (f" · ~{t['mencoes']} de {t['de_n_reviews']} "
                              f"reviews ({t['fracao_pct']}%)")
                if not p["pode_citar_numero"]:
                    linha += " · NÃO cite número nem frequência deste tema"
                L.append(linha)
                if t.get("exemplo"):
                    L.append(f"        ex.: {t['exemplo']}")
            if g["temas_omitidos"]:
                L.append(f"  ({g['temas_omitidos']} tema(s) menos frequente(s) "
                         f"omitido(s) de propósito — não os mencione)")
        L.append("")
    return "\n".join(L)


# ===========================================================================
# O prompt do narrador sob briefing — só o que NÃO é computável
# ===========================================================================

PROMPT_NARRADOR_BRIEFING = """\
Você recebe um BRIEFING com todas as decisões já tomadas: quais temas usar, \
em que ordem, com que palavra de frequência, quantas frases por movimento. \
Sua ÚNICA tarefa é transformar isso em prosa corrida, em português do \
Brasil. Você NÃO escolhe tema, NÃO calcula número, NÃO decide ordem — tudo \
isso já está resolvido no briefing.

O texto tem TRÊS MOVIMENTOS, sem subtítulos e sem marcações entre eles (a \
divisão organiza você, não aparece para o leitor):

MOVIMENTO 1 — O FILME: a premissa, a partir da sinopse do briefing, mais \
diretor, gênero e ano. Se o orçamento deste movimento for 0, pule-o e comece \
direto no movimento 2.

MOVIMENTO 2 — A EXPERIÊNCIA: como é assistir ao filme. Use o MATERIAL DO \
MOVIMENTO 2 do briefing (a lista com todos os temas de todos os grupos) \
para achar o que serve aqui, usando só propriedades DESCRITIVAS (ritmo, tom, atmosfera, intensidade, estrutura, \
ambientação, densidade) que apareçam em MAIS DE UM grupo com o mesmo núcleo \
factual. Tom NEUTRO, sem valência: aqui se descreve, não se julga. É \
PROIBIDO juízo de qualidade (atuações boas/ruins, roteiro \
inteligente/fraco) — isso é sempre disputado e pertence ao movimento 3. Se \
menos de duas propriedades servirem, este movimento fica com UMA frase ou \
é OMITIDO — omitir é o comportamento correto, e preencher com elogio \
suavizado ("estilo eficaz", "abordagem arrojada") é pior do que não ter o \
movimento.

MOVIMENTO 3 — O CONTRASTE: as perspectivas dos grupos, NA ORDEM que o \
briefing fixa, cada um com os temas que o briefing lista. Dê mais espaço ao \
primeiro grupo da ordem e menos ao último.

REGRAS (todas obrigatórias):
1. FIDELIDADE: toda afirmação vem do briefing. É PROIBIDO acrescentar fato, \
opinião própria ou qualquer contexto externo sobre o filme, elenco, direção \
ou produção. Se não está no briefing, não existe.
2. ANTI-SPOILER: em QUALQUER movimento, é PROIBIDO citar eventos de trama, \
personagens específicos ou desfecho — inclusive a partir da sinopse.
3. NÚMEROS: use exatamente os números do briefing. É PROIBIDO calcular, \
arredondar, somar ou inventar qualquer número — inclusive nota média, score \
ou "X de 10". Para a FREQUÊNCIA de cada tema, o briefing dá um CONJUNTO de \
construções equivalentes: escolha uma delas e VARIE entre os temas — \
repetir a mesma construção em tema após tema é o defeito que esta regra \
existe para evitar. Usar construção fora do conjunto do tema é PROIBIDO: \
diria uma faixa diferente da medida.
4. VOCABULÁRIO DO PESO: o rótulo de peso vem do histograma de NOTAS. \
Escreva sempre "das notas"; é PROIBIDO escrever "das reviews", "dos \
espectadores" ou "do público" ao falar de peso.
5. PERSPECTIVA: quando o briefing pedir marcacao_perspectiva "simples", \
inclua ao menos um marcador dentro do trecho do grupo ("para eles", "nessa \
leitura", "para quem está nessa faixa"); quando pedir "antecipada", o \
marcador vem ANTES da primeira afirmação sobre o grupo. É PROIBIDO marcador \
com carga depreciativa ("apenas para eles", "só para esses poucos").
6. MINORIA: o grupo de menor peso recebe menos espaço, mas a mesma \
seriedade — sem ironia e sem insinuar que quem pensa assim está errado.
7. ESCOPO: cada afirmação é atribuída ao SEU grupo. É PROIBIDO generalizar \
para "os críticos", "o público" ou "o consenso".
8. FORMA: português do Brasil, sem aspas de citação, sem subtítulos, entre \
250 e 400 palavras. Separe os movimentos em PARÁGRAFOS — pelo menos um \
parágrafo por movimento escrito, separados por linha em branco, e nenhum \
parágrafo com mais de 180 palavras. Um bloco corrido único não é aceitável.

Não se preocupe com ritmo ou elegância — um estágio seguinte de edição \
cuida disso e não pode alterar nenhum número ou atribuição seus.

Responda APENAS com JSON puro: {"narrativa": "<seu texto>"}"""
