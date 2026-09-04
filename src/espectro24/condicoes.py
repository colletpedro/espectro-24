"""[v1.9.35, §0 terceira exceção] CONDIÇÕES DE DECISÃO — recomendação
condicional ancorada em tema publicado.

**O que o bloco é.** Duas colunas no topo de `filme.html`, cada uma com até
cinco frases curtas que completam uma abertura fixa:

    Vale a pena se você...    quer um retrato íntimo, não o estadista
    Talvez evite se você...   quer rigor histórico

**A mudança de natureza, e ela está registrada no §0.** O §3[V] abre dizendo
que o veredito *"não é recomendação"*. Isso continua valendo do VEREDITO e
deixa de valer deste bloco: a condição diz ao leitor em que caso assistir.
A exceção é deliberada, tem parágrafo próprio no §0, e é sustentada por três
garantias que não são opcionais — proveniência visível, seleção de tema em
CÓDIGO, e leitura humana de 100% antes de publicar.

**A fronteira do §3[V] vale aqui INTEGRALMENTE:** o código decide O QUÊ
(quais temas, de qual grupo, em que ordem, com que rótulo de força, com que
peso); o modelo decide apenas COMO ESCREVER. A rodada 1 do estudo mediu o
que acontece quando essa fronteira é afrouxada: deixando o modelo escolher os
temas, ele divergiu da ordem de frequência em **14 de 16** casos e descartou,
em `the-godfather`, o terceiro tema mais citado do grupo (18 de 40).

**Não consome `eixos`.** Nem lift, nem margem, nem `contraste`, nem
`taxonomia_id`. O insumo é `buckets[].temas` — o que desacopla este bloco
inteiro da maquinaria da margem (§2.5).
"""
from __future__ import annotations

import re
import time
import unicodedata

from . import qualidade as q
from . import quantificador as Q
from . import synthesize as S
from . import veredito as V
from .config import BEST_OF_N, SPEC_VERSION

ESTAGIO = "condicoes"

# --- parâmetros do estágio, todos declarados ------------------------------

N_POR_LADO = 3              # base; o par obrigatório pode acrescentar
TETO_PALAVRAS = 14
MAX_POR_LADO = 6            # teto duro depois do par obrigatório

CODIGO_BUCKET = {"negativas": "NEG", "medianas": "MED", "positivas": "POS"}
LETRAS = "ABCDEFGH"
LADOS = ("vale_a_pena", "talvez_evite")
BUCKET_DO_LADO = {"vale_a_pena": "positivas", "talvez_evite": "negativas"}

# §3[C3]: `sem_numero` entrega tema SEM número e SEM quantificador verbal;
# `sem_quantificador` entrega frequência mas sem quantificador verbal. Nos
# dois, `rotulo_forca` NÃO pode ser emitido. O PESO (`share_real`) continua
# podendo — ele vem do histograma de NOTAS e não depende de haver review com
# texto, e suprimi-lo reintroduziria a infidelidade por omissão da v1.4.0.
ESTADOS_SEM_ROTULO = frozenset({"sem_numero", "sem_quantificador",
                                "sem_analise"})

# Teto da sequência copiável do `exemplo_parafraseado`. QUATRO, CALIBRADO
# sobre as 48 condições da rodada 1 do estudo, não herdado por analogia.
# Distribuição medida: 1 palavra: 8 · 2: 20 · 3: 15 · 4: 5 · 5+: 0.
# Em 3 reprovaria 41,7%, e a leitura mostra que a maioria é ENUMERAÇÃO sem
# sinônimo ("fotografia figurinos cenarios", "erros datas eventos") — o falso
# positivo caro que o §3[V] mediu três vezes. Em 4 reprova 10,4%, e os cinco
# são reconhecivelmente a frase de outra pessoa.
MAX_SEQ_EXEMPLO = 4

# [v1.9.37] Limiar do `peso_meio`, enunciado como o DEFEITO foi medido: a
# linha entra quando **as duas colunas somam menos de 80% das notas**.
#
# **Por que sobre a soma das colunas e não sobre o share do meio.** É a mesma
# fronteira, mas a formulação direta é a do achado da rodada 3 ("em 9 dos 35
# filmes as duas colunas somam menos de 80%") e não depende de arredondamento
# do terceiro bucket. Escrito como `share_meio >= 20` o critério pegaria
# `pearl-2022`, cujas colunas somam **81%** — um filme que o defeito medido
# não inclui. A régua tem de ser a do defeito, não uma proxy dele.
#
# **25 foi considerado e recusado, e o registro fica porque era o mais
# elegante:** é a fronteira inferior da faixa `muitos` do mapa de
# quantificador, que o projeto já reusou uma vez para exatamente "não é ruído,
# é fatia real" (`PISO_ASSUNTO_COMPARTILHADO_PCT`, §3[V]). Mas ali `barbie` e
# `mother-2017` ficariam de fora, e os dois somam 78% — ainda enganoso. Dois
# dos nove casos que a linha existe para cobrir é caro demais para pagar por
# um precedente bonito.
SOMA_MINIMA_DAS_COLUNAS_PCT = 80


# ===========================================================================
# Indexação — todos os temas do filme, a base dos validadores
# ===========================================================================

def indexar(output: dict) -> dict:
    """`id -> tema`, para os TRÊS buckets.

    Os ids são LETRAS e não números, e isso não é notação: um id `POS-3`
    poria algarismo na serialização do briefing, que é onde o §3[V] comprou
    a garantia "zero dígitos por construção".
    """
    idx = {}
    for b in output.get("buckets") or []:
        nome = b.get("bucket")
        if nome not in CODIGO_BUCKET:
            continue
        estado = b.get("estado_piso") or "completa"
        modo = b.get("modo") or "completo"
        for i, t in enumerate(b.get("temas") or []):
            if i >= len(LETRAS):
                break
            pct, rot = Q.fracao_e_rotulo(t["mencoes_aproximadas"],
                                         t["n_reviews_analisadas"])
            idx[f"{CODIGO_BUCKET[nome]}-{LETRAS[i]}"] = {
                "id": f"{CODIGO_BUCKET[nome]}-{LETRAS[i]}",
                "bucket": nome,
                "ordem": i,
                "tema": t["tema"],
                "exemplo": t["exemplo_parafraseado"],
                "mencoes": t["mencoes_aproximadas"],
                "de_n": t["n_reviews_analisadas"],
                "freq_pct": pct,
                "rotulo_forca": None if estado in ESTADOS_SEM_ROTULO else rot,
                "estado_piso": estado,
                "modo": modo,
                "share_pct": (b.get("share_real")
                              if isinstance(b.get("share_real"), int) else None),
            }
    return idx


# ===========================================================================
# Casamento lexical — herdado da v1.9.22, não reimplementado
# ===========================================================================

def _prefixos(texto: str) -> set[str]:
    return {w[:V.PREFIXO_PALAVRA] for w in V.palavras_de_conteudo(texto or "")}


def _prefixos_do_tema(t: dict) -> set[str]:
    return _prefixos(t["tema"] + " " + t["exemplo"])


def mesmo_assunto(t1: dict, t2: dict) -> bool:
    """Dois temas falam do MESMO assunto quando compartilham ao menos duas
    palavras de conteúdo. É a régua da âncora, reusada — não um limiar novo."""
    return len(_prefixos_do_tema(t1) & _prefixos_do_tema(t2)) >= 2


def _seq_maxima(texto: str, alvo: str) -> int:
    """Maior sequência de palavras de conteúdo do `texto` que aparece, na
    mesma ordem e contígua, no `alvo`."""
    A, B = V.palavras_de_conteudo(texto), V.palavras_de_conteudo(alvo)
    melhor = 0
    for i in range(len(A)):
        for j in range(len(B)):
            k = 0
            while i + k < len(A) and j + k < len(B) and A[i + k] == B[j + k]:
                k += 1
            if k > melhor:
                melhor = k
    return melhor


def _sem_acento(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s)
                   if not unicodedata.combining(c))


def palavras_copiaveis(tema: str) -> list[str]:
    """As palavras de conteúdo de um `tema` que contam para `tema_verbatim`,
    **excluídos os NOMES PRÓPRIOS**.

    [v1.9.35] A exceção existe porque nomear uma personagem exige o nome
    dela. MEDIDO na rodada 2 do estudo: 3 dos 5 disparos de `tema_verbatim`
    eram `Descaracterização do Arthur Fleck` — 3 palavras de conteúdo, o
    mínimo que aciona a regra, e **duas delas são o nome**.

    A fronteira é TIPOGRÁFICA porque o dado a carrega: token Capitalizado
    fora da primeira posição do tema. Mesma família da correção de fronteira
    da v1.9.22 (`tom` casando dentro de "tomam"), com o marcador de fronteira
    que o campo oferece.
    """
    brutos = re.findall(r"[^\W\d_]+", tema or "", flags=re.UNICODE)
    proprios = {_sem_acento(w).lower() for i, w in enumerate(brutos)
                if i > 0 and w[:1].isupper()}
    return [w for w in V.palavras_de_conteudo(tema) if w not in proprios]


# ===========================================================================
# SELEÇÃO — do CÓDIGO, nunca do modelo
# ===========================================================================

def selecionar(idx: dict, n: int = N_POR_LADO, *, par_obrigatorio: bool = True
               ) -> dict:
    """Os temas de cada lado.

    **BASE — os N primeiros na ORDEM PUBLICADA.** MEDIDO sobre 105 buckets
    dos JSONs de `resultado/`: a ordem publicada de `buckets[].temas` é
    `mencoes_aproximadas` DECRESCENTE em **105 de 105**, e é o único
    desempate existente nos **40** buckets com empate. Ordenar por `mencoes`
    e usar a ordem publicada são a MESMA seleção; a segunda também desempata.

    A razão de escolher a ordem publicada não é estatística, é de produto:
    os bullets já saem nela, na mesma tela, logo abaixo. Uma régua diferente
    poria duas ordenações divergentes da mesma evidência na mesma página.

    **PAR OBRIGATÓRIO.** Um tema selecionado cujo irmão de mesmo assunto no
    bucket oposto ficou de fora força esse irmão para dentro do outro lado.
    É o que impede a página de recomendar um traço sem mostrar a objeção que
    o outro grupo faz ao MESMO traço — o caso `napoleon`/batalhas, em que os
    três grupos acham as batalhas bonitas e só as HATERS dizem que elas
    carecem de tática.

    Duas invariantes do par obrigatório, as duas com razão registrada:

    - **calculado UMA vez sobre a seleção base, nunca em cascata.** Iterar
      tornaria a saída dependente da ordem em que os lados são varridos —
      a mesma instabilidade que o snapshot de aberturas do §3[V] existe para
      impedir;
    - **ACRESCENTA, nunca substitui.** A lista de bullets do §2.5 já tem
      tamanho variável ("no máximo 5, no mínimo 2, e o número de entradas é
      informação, não defeito de preenchimento"); deslocar o último
      selecionado trocaria uma omissão por outra.
    """
    base = {}
    for lado, bucket in BUCKET_DO_LADO.items():
        do_bucket = sorted((t for t in idx.values() if t["bucket"] == bucket),
                           key=lambda t: t["ordem"])
        base[lado] = do_bucket[:n]
    if not par_obrigatorio:
        return base

    sel = {lado: list(v) for lado, v in base.items()}
    for lado in LADOS:
        outro = "talvez_evite" if lado == "vale_a_pena" else "vale_a_pena"
        oposto = BUCKET_DO_LADO[outro]
        ja = {t["id"] for t in base[outro]}
        forcados: list[dict] = []
        for t in base[lado]:
            candidatos = sorted(
                (o for o in idx.values()
                 if o["bucket"] == oposto and o["id"] not in ja
                 and o["id"] not in {f["id"] for f in forcados}
                 and mesmo_assunto(t, o)),
                key=lambda o: o["ordem"])
            if candidatos:
                forcados.append(candidatos[0])
        sel[outro] = sorted(base[outro] + forcados,
                            key=lambda t: t["ordem"])[:MAX_POR_LADO]
    return sel


# ===========================================================================
# ORDEM DAS COLUNAS — por peso (v1.9.30), herdada
# ===========================================================================

# Desempate: a ordem canônica do produto (negativas antes de positivas), como
# critério EXPLÍCITO e não como efeito colateral da estabilidade do `sort`.
_ORDEM_CANONICA = {"talvez_evite": 0, "vale_a_pena": 1}


def ordem_das_colunas(idx: dict) -> list[str]:
    """Os lados, do maior `share_real` para o menor.

    **Herdado da v1.9.30, não reinventado.** O argumento é o daquela versão,
    trocando "bloco" por "coluna": *"a ordem antiga não era neutra — era
    CONSTANTE, que é outra coisa… quando duas posições são desiguais por
    construção, a única regra defensável é a que decide entre elas pelo
    DADO."* Em `the-godfather` (2/5/93) a leitura passa a abrir por quem
    recomenda; em `cats-2019` (86/7/7), por quem não recomenda.
    """
    def peso(lado: str):
        bucket = BUCKET_DO_LADO[lado]
        for t in idx.values():
            if t["bucket"] == bucket and t["share_pct"] is not None:
                return t["share_pct"]
        return -1
    return sorted(LADOS, key=lambda l: (-peso(l), _ORDEM_CANONICA[l]))


def peso_do_lado(idx: dict, lado: str) -> dict:
    """[v1.9.35, correção 1b] O PESO daquela coluna, escrito em CÓDIGO.

    **Este é o conserto da razão nº 1** do estudo: o formato de condição é
    simétrico por construção, e `the-godfather` (2/5/93) publicava três
    frases de cada lado com o mesmo peso visual — a infidelidade por omissão
    da v1.4.0 reaparecendo num canal novo.

    **`rotulo_forca` foi MEDIDO como incapaz de fechar isso:** em 18 de 35
    filmes o rótulo do topo do lado minoritário é igual ou mais forte que o
    do majoritário (`cidade-de-deus`, 1% × 96%, dá *muitos* nos dois), e em
    `napoleon-2023` ele aponta para o lado errado. A razão é estrutural —
    `rotulo_forca` é `mencoes/n_analisadas` DENTRO do bucket, e o
    desequilíbrio é ENTRE buckets.

    A forma é a do `prefixo_de_codigo` do §3[V], reusada: número concatenado
    pelo CÓDIGO, fora da saída do modelo.

    `nota_de_amostra` é a segunda metade, e cobre a outra ausência que o
    estudo registrou: o veredito diz *"numa amostra pequena"* e as condições
    não diziam.
    """
    bucket = BUCKET_DO_LADO[lado]
    do_bucket = [t for t in idx.values() if t["bucket"] == bucket]
    if not do_bucket:
        return {"peso_pct": None, "peso_texto": None, "nota_de_amostra": None}
    t = do_bucket[0]
    reduzida = t["modo"] == "reduzido" or t["estado_piso"] != "completa"
    pct = t["share_pct"]
    return {
        "peso_pct": pct,
        # O peso vem do histograma de NOTAS e é publicável mesmo em bucket de
        # piso (§3[C3]) — o piso suprime o QUANTIFICADOR, nunca o peso.
        "peso_texto": None if pct is None else f"~{pct}% das notas",
        "nota_de_amostra": "amostra pequena" if reduzida else None,
    }


# ===========================================================================
# [v1.9.36] RISCO DE SPOILER — marca de BRIEFING, deliberadamente NÃO validador
# ===========================================================================
# **O achado da rodada 3, e ele é do FORMATO.** O filtro de spoiler de §3[D]
# roda sobre os TEMAS e não basta, porque a condição muda a FORÇA
# ILOCUCIONÁRIA: o bullet "Monólogo final" relata o que comentaram; a condição
# "vale a pena se você espera um monólogo final devastador" instrui o leitor
# sobre o que aguardar. Mesmo conteúdo, ato de fala diferente — e é o segundo
# que estraga o filme.
#
# **Por que isto NÃO é um validador, e a decisão é medida.** Rodado sobre as
# 266 condições da rodada 3, o marcador dispara em 19 (7,1%) e pega 3 dos 5
# casos que a leitura humana marcou: **precisão de 15,8%**. Pior que o léxico
# de valência que a rodada 3 REMOVEU por 7,7%, e com o mesmo modo de falha
# caro — falso positivo aqui descartaria condição boa, que é o custo que o
# §3[V] mediu três vezes na primeira geração dos 35.
#
# **Por que ele entra assim mesmo, e a razão é ASSIMETRIA DE CUSTO.** Como
# validador, um falso positivo joga fora uma condição boa. Como marca no
# BRIEFING, um falso positivo só faz o modelo escrever com mais cuidado sobre
# aquele tema. Um sinal de baixa precisão é utilizável no lado barato e não no
# lado caro — e parte dos "falsos positivos" medidos é subcontagem da leitura
# humana, não erro do marcador ("desfecho explosivo", "pontas soltas no
# final", "reviravoltas surpreendentes" são casos que a regra nova deve pegar
# e que a rodada 3 não marcou).
#
# A rede declarada continua sendo a regra 9 do prompt mais a leitura humana.
# CONVENÇÃO: `*` casa por prefixo; sem `*`, token inteiro (v1.9.22).
_MARCADORES_SPOILER = (
    "final", "finais", "desfecho", "desfechos", "reviravolta", "reviravoltas",
    "twist", "revelac*", "morte", "morre", "morrem", "climax", "clim*",
    "encerrament*", "conclusa*", "despedida*", "ultimo", "ultima",
    "ponto de chegada", "descobre", "descoberta", "segredo", "identidade",
)

_RE_SPOILER = [
    re.compile(rf"(?<![a-z]){re.escape(m.rstrip('*'))}"
               + ("" if m.endswith("*") else r"(?![a-z])"))
    for m in _MARCADORES_SPOILER
]


def risco_de_spoiler(tema: dict) -> bool:
    """O tema carrega linguagem de desfecho/revelação na paráfrase?

    Proxy declarado, de baixa precisão (15,8% medida), usado só para MARCAR o
    briefing. Nunca reprova nada.
    """
    plano = V._normalizar((tema.get("tema") or "") + " " + (tema.get("exemplo") or ""))
    return any(r.search(plano) for r in _RE_SPOILER)


def peso_do_meio(idx: dict) -> dict | None:
    """[v1.9.37] O peso do MEIO-TERMO, quando ele é grande e não tem coluna.

    **O defeito que isto fecha.** O bloco tem duas colunas e o meio não é uma
    delas (o meio nunca é um dos dois lados — mesma regra do §3[V]). Em
    `napoleon-2023` o leitor vê `~33% das notas` e `~22% das notas` e **45%
    ficam invisíveis**: os dois números são verdadeiros e o conjunto sugere
    que somam o filme inteiro. É a infidelidade por omissão da v1.4.0 numa
    terceira forma — não mais entre os dois grupos, mas entre eles e o resto.

    Escrito em CÓDIGO e concatenado fora da saída do modelo, no mesmo
    estatuto de `peso_texto` e `nota_de_amostra`. Precedente literal: o
    `prefixo_de_codigo` do §3[V], que já faz isso quando o meio é DOMINANTE.
    Esta função cobre o caso em que o meio é grande **sem** ser o maior.

    `None` abaixo do piso: em `the-godfather` (2/5/93) uma terceira linha
    dizendo "~5% ficaram no meio" acrescenta ruído sem informar.
    """
    share = {}
    for t in idx.values():
        if t["share_pct"] is not None:
            share[t["bucket"]] = t["share_pct"]
    meio = share.get("medianas")
    colunas = share.get("negativas"), share.get("positivas")
    if meio is None or None in colunas:
        return None
    if sum(colunas) >= SOMA_MINIMA_DAS_COLUNAS_PCT:
        return None
    return {"pct": meio,
            "texto": f"~{meio}% das notas ficaram no meio-termo"}


# ===========================================================================
# Briefing — só os temas escolhidos, na ordem escolhida, zero algarismo
# ===========================================================================

_NOME = {"negativas": "QUEM NÃO RECOMENDA", "positivas": "QUEM RECOMENDA"}


def montar_briefing(output: dict) -> dict | None:
    """O documento de decisões do estágio. Código puro, zero LLM.

    `None` quando não há tema nenhum nos dois buckets extremos — mesma
    política aditiva de `ficha` (§3[F]) e `distribuicao` (§3[G]): sem o
    insumo, a chave não é emitida, nunca um bloco montado sobre buraco.
    """
    idx = indexar(output)
    sel = selecionar(idx)
    if not any(sel[l] for l in LADOS):
        return None
    dominante = None
    melhor = -1
    for t in idx.values():
        if t["share_pct"] is not None and t["share_pct"] > melhor:
            melhor, dominante = t["share_pct"], t["bucket"]
    return {
        "slug": output.get("slug"),
        "idx": idx,
        "selecao": sel,
        "ordem_colunas": ordem_das_colunas(idx),
        "peso": {l: peso_do_lado(idx, l) for l in LADOS},
        "peso_meio": peso_do_meio(idx),
        "meio_dominante": dominante == "medianas",
    }


def serializar_briefing(b: dict) -> str:
    """O briefing como texto, para a mensagem do usuário.

    **Nenhum algarismo sai daqui, e o título do filme também não** — as duas
    garantias do §3[V], herdadas literalmente. O título fica de fora porque
    nomear o filme convida o modelo a usar o que ele sabe sobre o filme, e a
    invariante de fidelidade proíbe contexto externo.

    O PESO e a NOTA DE AMOSTRA não entram: são concatenados pelo código na
    renderização, fora da saída do modelo. Determinística.
    """
    L: list[str] = []
    for lado in b["ordem_colunas"]:
        bucket = BUCKET_DO_LADO[lado]
        L.append(f"{_NOME[bucket]} — ESCREVA UMA CONDIÇÃO PARA CADA TEMA "
                 f"ABAIXO, NESTA ORDEM (lado `{lado}`):")
        if not b["selecao"][lado]:
            L.append("  (nenhum tema disponível neste grupo — devolva lista "
                     "VAZIA para este lado)")
        for t in b["selecao"][lado]:
            L.append(f"  [{t['id']}] {t['tema']}")
            L.append(f"       o que o grupo diz: {t['exemplo']}")
            if t["estado_piso"] != "completa" or t["modo"] == "reduzido":
                L.append("       AMOSTRA PEQUENA neste grupo: não afirme "
                         "quantidade, nem em palavra.")
            if risco_de_spoiler(t):
                # Sem número de regra: o briefing é o texto que carrega DADO
                # do filme, e a garantia "zero algarismo por construção" vale
                # sobre ele inteiro. Citar "a regra 9" aqui a quebraria — e
                # `test_briefing_nao_tem_algarismo_em_nenhum_dos_35` pegou
                # exatamente isso na primeira escrita desta linha.
                L.append("       ATENÇÃO — este tema toca desfecho, "
                         "reviravolta ou revelação. Você PODE dizer que o "
                         "final é aberto ou que a obra tem uma virada; NÃO "
                         "pode dizer o que o final contém nem o EFEITO da "
                         "virada sobre a compreensão do filme. Sem "
                         "formulação com lastro, SALTE o tema.")
        L.append("")
    if b["meio_dominante"]:
        L += ["O MEIO-TERMO É O MAIOR GRUPO DA RECEPÇÃO. O peso dos grupos é "
              "informado por fora, pelo sistema — não escreva número.", ""]
    return "\n".join(L).rstrip() + "\n"


PROMPT_CONDICOES = """\
Você escreve CONDIÇÕES DE DECISÃO de um filme, para quem AINDA NÃO ASSISTIU \
e está decidindo se assiste.

Uma condição é uma frase curta que completa uma destas duas aberturas:

  "Vale a pena se você..."      (lado vale_a_pena)
  "Talvez evite se você..."     (lado talvez_evite)

**O que uma condição É.** Uma janela para o filme: ela nomeia algo CONCRETO \
que a recepção encontrou, e deixa o leitor reconhecer sozinho se aquilo lhe \
interessa. O enquadramento inteiro da tarefa é este:

  "estas são experiências e qualidades que a recepção encontrou neste filme; \
  veja se alguma é o que você procura — ou o que você quer evitar."

Este é o registro certo, e são frases reais do produto:

  · aprecia uma direção marcante com fotografia dinâmica e forte apelo visual
  · valoriza atuações comoventes guiadas por expressões sutis e silêncios \
expressivos
  · busca uma experiência meditativa e aceita um ritmo vagaroso para \
mergulhar no personagem

**O que uma condição NÃO é, dos dois lados.** Não é um PERFIL PSICOLÓGICO do \
leitor — é PROIBIDO escrever "você é o tipo de pessoa que", "pessoas que", ou \
converter cada frase numa preferência artificial. E também não é repetição de \
crítica ("o filme tem ótima fotografia"). Fique no meio: a qualidade concreta \
da obra, oferecida ao reconhecimento do leitor.

**É PROIBIDO inventar uma OPOSIÇÃO que a paráfrase não tem.** Trocar "aprecia \
uma direção marcante com fotografia dinâmica" por "prioriza impacto visual em \
vez de uma abordagem discreta" é PIOR, não melhor: perde a qualidade concreta \
e inventa um contraste que as reviews talvez não tenham feito. Só use a forma \
"X em vez de Y" quando os DOIS lados estiverem na paráfrase.

Você recebe os TEMAS JÁ ESCOLHIDOS, com um código entre colchetes. **Você \
NÃO escolhe quais temas usar e NÃO reordena.** Escreva UMA condição para \
CADA tema recebido, na ordem em que vieram, no lado em que ele veio.

REGRAS (todas obrigatórias):

1. ÂNCORA. Toda condição cita o código do SEU tema, e o texto tem de nomear \
o assunto daquele tema com pelo menos duas palavras de conteúdo dele ou do \
que o grupo diz sobre ele.

2. FIDELIDADE. Só existe o que está no tema recebido. É PROIBIDO introduzir \
assunto, adjetivo avaliativo, nome de pessoa ou informação de enredo que não \
esteja ali.

3. SINAL. A condição não pode afirmar mais do que o tema afirma. Se o tema \
descreve um EFEITO ("o filme despertou curiosidade"), a condição não pode \
convertê-lo em APROVAÇÃO de outra coisa ("não se incomoda com imprecisão"). \
Se o tema descreve INCÔMODO, não vire TOLERÂNCIA. Se o tema diz "bonito mas \
sem tática", a condição não pode dizer só "bonito".

4. DISCRIMINAÇÃO. A condição precisa dizer QUAL leitura ela oferece — a \
palavra que separa essa leitura de outra sobre o mesmo assunto tem de estar \
nela. "quer ritmo lento" não serve quando um grupo chama isso de tédio e o \
outro de contemplação; "quer um ritmo contemplativo" serve.

5. RESSALVA DO PRÓPRIO TEMA. Se o texto do grupo trouxer uma ressalva ("mas \
alguns acham...", "embora...", "apesar de..."), a condição NÃO pode ficar só \
com a metade que convém. Ou ela carrega as duas, ou você salta o tema.

6. ABSTENÇÃO — SALTE O TEMA. Se de um tema recebido não sair uma condição \
honesta, **não escreva nada para ele e passe ao seguinte**. É PROIBIDO \
substituí-lo por outro assunto e é PROIBIDO completar cota. Devolver menos \
condições do que temas recebidos é uma resposta CORRETA, e devolver lista \
VAZIA também é. Saltar é sempre melhor que forçar: uma vaga vazia não engana \
ninguém, uma condição forçada engana.

7. ZERO DÍGITOS. Nenhum algarismo, em nenhuma forma.

8. NADA DE QUANTIDADE. É PROIBIDO escrever "a maioria", "muitos", "alguns", \
"poucos", "cerca de metade", "quase todos" ou qualquer outra palavra sobre \
quantas pessoas disseram aquilo. Esse rótulo é do sistema e aparece ao lado \
da sua frase — se você escrever um, ele vai contradizer o do sistema.

9. ANTI-SPOILER — e a unidade a proteger é a CONDIÇÃO PUBLICADA, não o \
tema. É PROIBIDO usar desfecho, reviravolta, ponto de chegada de arco, morte, \
revelação final ou qualquer informação cujo valor dependa de o espectador \
ainda não conhecê-la como MOTIVO para recomendar ou desaconselhar o filme. \
A regra vale **mesmo quando o tema de origem é válido** e **mesmo quando a \
review menciona o elemento**: o tema RELATA o que as pessoas comentaram, e a \
sua frase INSTRUI o leitor sobre o que aguardar — e é a segunda coisa que \
estraga o filme.

9b. O TESTE OPERACIONAL, e é ele que decide os casos difíceis: **se a sua \
frase diz ao leitor O QUE PROCURAR durante o filme, é spoiler. Se diz apenas \
QUE TIPO DE EXPERIÊNCIA é, não é.**

9c. A ESTRUTURA DO FINAL É PERMITIDA; O CONTEÚDO DELE NÃO. Você PODE dizer \
que o filme termina de forma ambígua, aberta ou sem resolver tudo — isso não \
revela nada da trama e é informação de decisão real, porque muita gente evita \
final aberto de propósito. Você NÃO PODE dizer o que o final contém, nem que \
ele reverte, recontextualiza ou revela alguma coisa.

  PERMITIDO: se frustra com narrativas que não oferecem uma resolução \
definitiva
  PROIBIDO:  se frustra com um final que revira tudo o que foi construído

9d. REVIRAVOLTA: NOMEAR é permitido, descrever o EFEITO não. Você PODE dizer \
que a obra tem uma reviravolta, uma virada ou uma revelação, quando o tema \
sustenta — filmes assim são conhecidos por isso e a reputação pública já \
carrega o fato. Você NÃO PODE descrever o EFEITO dela sobre a compreensão do \
filme: que ela transforma a história, muda a perspectiva, recontextualiza o \
que veio antes, ou faz o leitor reinterpretar o que viu. **É o efeito que \
manda o leitor assistir procurando.**

  PERMITIDO: procura um suspense psicológico construído em torno de uma virada
  PROIBIDO:  gosta de reviravoltas que transformam a história
  PROIBIDO:  aprecia uma mudança memorável de perspectiva na trama

9e. QUANDO O TEMA FOR ÚTIL MAS ARRISCADO, ABSTRAIA O ACONTECIMENTO e preserve \
a experiência:

  RUIM:       espera um monólogo final devastador
  PREFERÍVEL: quer uma atuação que sustente um momento de fúria e \
vulnerabilidade

9f. PRECEDÊNCIA. O anti-spoiler **REBAIXA o teto de abstração disponível** \
(regra 13). Se a única formulação que evita o \
spoiler já não tiver lastro pleno na paráfrase, a resposta é **SALTAR O \
TEMA** — nunca escolher a menos pior. É PROIBIDO sacrificar lastro para caber \
nesta regra.

9g. EXPECTATIVA E REPUTAÇÃO SÃO ASSUNTO LEGÍTIMO, e não são spoiler. Quando o \
tema fala de hype, de o filme ser considerado superestimado, ou de a \
expectativa não ter sido correspondida, **escreva a condição normalmente**. \
Isso é informação de decisão de primeira ordem. Formule pela RELAÇÃO entre a \
reputação da obra e o que ela entrega — não pelo estado mental de quem \
assiste:

  BOM:  se frustra quando obras de grande reputação não correspondem a altas \
expectativas
  BOM:  procura um filme à altura da fama que o precede
  RUIM: é o tipo de pessoa que cria expectativas altas demais

10. ESCOPO. É PROIBIDO falar de "os críticos", "o consenso", "a recepção do \
filme" ou "o público".

11. PALAVRAS SUAS. É PROIBIDO copiar o tema OU o texto do "o que o grupo \
diz" palavra por palavra. Sem aspas.

12. FORMA. No máximo quatorze palavras por condição, português do Brasil, \
começando em minúscula, continuando a abertura sem repeti-la.

13. ESPECIFICIDADE — use a MAIOR abstração que continue TOTALMENTE \
sustentada pela paráfrase. Um detalhe incidental não vira critério central: \
se a paráfrase elogia os visuais e cita de passagem um elemento específico, a \
condição fala dos VISUAIS, não do elemento. **E não generalize \
automaticamente:** subir de abstração só é permitido enquanto cada palavra \
continuar sustentada. Abstrair além disso é inventar; especificar além disso \
é transformar observação de uma pessoa em promessa ao leitor.

Responda APENAS com JSON puro:
{"vale_a_pena": [{"texto": "...", "tema_origem": "POS-A"}],
 "talvez_evite": [{"texto": "...", "tema_origem": "NEG-A"}]}"""


# ===========================================================================
# Validações pós-parsing — em CÓDIGO, nunca só no prompt
# ===========================================================================
#
# **VALIDADOR 1 — ÂNCORA OBRIGATÓRIA**, em quatro sub-regras decidíveis:
#   1a `tema_origem` existe na lista de temas DAQUELE filme (pertinência de
#      conjunto — a parte forte, zero folga);
#   1b o tema citado é do BUCKET do lado (v1.9.35, substitui o validador de
#      corroboração por valência — ver a nota abaixo);
#   1c o TEXTO casa lexicalmente com o tema citado, senão o código é carimbo.
#      Casamento por PALAVRA DE CONTEÚDO e PREFIXO DE 5, herdado da v1.9.22 —
#      nunca por substring, porque substring premia cópia verbatim. Julga
#      contra `tema` E `exemplo_parafraseado`, herança direta de P4 REVISADO
#      (§2.7): é a paráfrase que carrega a afirmação específica;
#   1d cópia literal REPROVA, não premia — do tema (`tema_verbatim`, com a
#      exceção de nome próprio) e da paráfrase (`exemplo_verbatim`).
#
# **VALIDADOR 2 — DISCRIMINAÇÃO.** Quando o assunto da condição também é
# assunto de outro bucket, a condição precisa carregar ao menos uma palavra
# que SEPARE a leitura citada da do outro grupo.
#
# > **O que este validador declaradamente NÃO pega, e está medido.** A
# > condição que empresta palavras suficientes para ancorar E discriminar e
# > ainda assim afirma outra proposição. `napoleon`/`POS-C` ("sequências de
# > batalha espetaculares") passa limpa, porque `espetaculares` é
# > lexicalmente exclusiva de `POS-C` embora semanticamente idêntica a
# > "visualmente impressionantes" das HATERS. O proxy é LEXICAL e o defeito é
# > SEMÂNTICO. **O que fecha aquele caso é o par obrigatório da seleção, não
# > um validador** — o leitor passa a ver as duas leituras.
#
# **[v1.9.35] O validador de CORROBORAÇÃO POR VALÊNCIA foi REMOVIDO.**
# MEDIDO na rodada 2 do estudo: dos 13 temas que o léxico classificou como de
# sinal oposto ao lado, **12 eram erro do léxico** (precisão 7,7%) — "Crítica
# à idolatria do Coringa", onde o filme É a crítica; "Remake subestimado",
# cuja paráfrase diz "recebeu críticas injustas". Produziu 2 flags
# falso-positivas em 196 condições e ZERO verdadeiras. É o mesmo modo de
# falha que o §3[V] corrigiu removendo `incomod*` ("incômodo é como se
# descreve QUALQUER coisa de que não se gostou"): palavra avaliativa em uso
# META quebra o léxico. Um validador que reprova mais texto correto do que
# errado é pior que não ter validador — ele empurra o filme para o fallback.
# No lugar entra `ancora_de_outro_bucket` (1b), que é exato e não tem léxico.
# **O resíduo fica declarado:** um tema que é ele próprio uma queixa dentro
# do bucket positivo continua indetectável por máquina; contra ele restam a
# regra de abstenção do prompt e a leitura humana.

_ASPAS = V._ASPAS
_ESCOPO_GENERALIZADO = V._ESCOPO_GENERALIZADO
_NOTA_OU_SCORE = V._NOTA_OU_SCORE

# Toda construção do mapa de quantificador é proibida ao modelo: o rótulo é
# do CÓDIGO e é exibido ao lado da frase (§0, "quantidade é do código").
from . import briefing as _br  # noqa: E402

_RE_QUANTIDADE = [
    re.compile(rf"(?<![a-z]){re.escape(V._normalizar(c))}(?![a-z])")
    for cs in _br.FAIXAS_QUANTIFICADOR.values() for c in cs
]


# [v1.9.36] PERFIL DE LEITOR — marca lexical ESTREITA, e só ela.
#
# O refinamento da rodada 4 separa duas coisas que o prompt antigo confundia:
# a condição nomeia uma QUALIDADE CONCRETA da obra e deixa o leitor se
# reconhecer; ela não descreve o leitor. O padrão caro ("prioriza X em vez de
# Y", oposição inventada que a paráfrase não tem) é SEMÂNTICO e não entra
# aqui — detectá-lo exigiria comparar alcance com a paráfrase, que é o erro
# que a rodada 3 removeu ao tirar o léxico de valência.
#
# O que entra é só o que é EXATO: a segunda pessoa explícita e a
# generalização sobre pessoas. Lista curta, de propósito.
_PERFIL_DE_LEITOR = (
    "voce e o tipo", "voce e daquele", "voce e daquelas", "se voce e",
    "pessoas que gostam", "pessoas que preferem", "quem e do tipo",
    "seu perfil", "o seu tipo",
)


def _validar_ancora(cond: dict, idx: dict) -> list[str]:
    tid = (cond.get("tema_origem") or "").strip().upper()
    t = idx.get(tid)
    if t is None:
        return ["ancora_inexistente"]                                    # 1a
    flags = []
    if t["bucket"] != BUCKET_DO_LADO.get(cond.get("lado")):              # 1b
        flags.append("ancora_de_outro_bucket")
    alvo = _prefixos_do_tema(t)
    if len(alvo & _prefixos(cond["texto"])) < min(2, len(alvo)):         # 1c
        flags.append("ancora_nao_verificavel")
    copiaveis = palavras_copiaveis(t["tema"])                            # 1d
    if len(copiaveis) >= 3 and _seq_maxima(cond["texto"], t["tema"]) >= len(
            V.palavras_de_conteudo(t["tema"])):
        flags.append("tema_verbatim")
    if _seq_maxima(cond["texto"], t["exemplo"]) >= MAX_SEQ_EXEMPLO:
        flags.append("exemplo_verbatim")
    return flags


def _validar_discriminacao(cond: dict, idx: dict) -> list[str]:
    tid = (cond.get("tema_origem") or "").strip().upper()
    t = idx.get(tid)
    if t is None:
        return []
    irmaos = [o for o in idx.values()
              if o["bucket"] != t["bucket"] and mesmo_assunto(t, o)]
    if not irmaos:
        return []
    compartilhado: set[str] = set()
    for o in irmaos:
        compartilhado |= _prefixos_do_tema(o)
    exclusivos = _prefixos_do_tema(t) - compartilhado
    if not (_prefixos(cond["texto"]) & exclusivos):
        return ["sem_discriminacao"]
    return []


def validar(cond: dict, idx: dict) -> list[str]:
    """As flags mecânicas de UMA condição. Lista ordenada, vazia = limpa."""
    texto = cond.get("texto") or ""
    if not texto.strip():
        return ["vazio"]
    plano = V._normalizar(texto)
    flags = []
    if q.formato_invalido(texto):
        flags.append("formato_invalido")
    if re.search(r"\d", texto):
        flags.append("digito")
    if any(c in texto for c in _ASPAS):
        flags.append("aspas")
    if len(re.findall(r"\S+", texto)) > TETO_PALAVRAS:
        flags.append("comprimento")
    if any(m in plano for m in _ESCOPO_GENERALIZADO):
        flags.append("escopo_generalizado")
    if any(re.search(p, plano) for p in _NOTA_OU_SCORE):
        flags.append("nota_ou_score")
    if any(r.search(plano) for r in _RE_QUANTIDADE):
        flags.append("quantidade_escrita")
    if not S._idioma_e_pt_br(texto):
        flags.append("idioma")
    if q.achar_resenha_speak(texto, q.carregar_blocklist()):
        flags.append("cliche")
    if any(m in plano for m in _PERFIL_DE_LEITOR):
        flags.append("perfil_de_leitor")
    flags += _validar_ancora(cond, idx)
    flags += _validar_discriminacao(cond, idx)
    return sorted(set(flags))


_EXPLICACAO = {
    "vazio": "veio vazia",
    "formato_invalido": "veio embrulhada em JSON/cerca de código",
    "digito": "contém algarismo — nenhum número pode sair de você",
    "aspas": "usa aspas de citação",
    "comprimento": f"passou do teto de {TETO_PALAVRAS} palavras",
    "escopo_generalizado": 'generaliza para "os críticos"/"o consenso"/"o '
                           'público" em vez de falar do GRUPO',
    "nota_ou_score": "menciona nota, estrela ou score",
    "quantidade_escrita": "escreve uma palavra de quantidade ('a maioria', "
                          "'alguns', 'poucos'). Esse rótulo é do sistema e "
                          "aparece ao lado da sua frase",
    "idioma": "não está em português do Brasil",
    "cliche": "usa expressão de resenha genérica",
    "ancora_inexistente": "cita um código de tema que não existe",
    "ancora_de_outro_bucket": "cita um tema do OUTRO grupo — cada lado só "
                              "usa os temas que recebeu",
    "ancora_nao_verificavel": "não nomeia o assunto do tema que diz citar: "
                              "use pelo menos duas palavras de conteúdo dele "
                              "ou do que o grupo diz",
    "tema_verbatim": "copia o tema palavra por palavra — diga o assunto com "
                     "as suas palavras",
    "exemplo_verbatim": "copia uma sequência do texto do grupo palavra por "
                        "palavra — reformule",
    "perfil_de_leitor": "descreve o LEITOR em vez de nomear a qualidade "
                        "concreta do filme. Diga o que a recepção encontrou "
                        "e deixe o leitor se reconhecer sozinho",
    "sem_discriminacao": "o outro grupo fala do MESMO assunto e a sua frase "
                         "não diz qual das duas leituras ela oferece: use a "
                         "palavra que separa uma da outra",
}


# ===========================================================================
# Parsing, seleção entre candidatos, e orquestração
# ===========================================================================

def extrair(bruto: str) -> dict:
    """As condições da resposta do modelo. Mesma tolerância de
    `veredito.extrair_veredito`: JSON bem formado no caminho normal, e o
    maior bloco `{...}` quando o modelo embrulha em prosa."""
    import json

    bruto = (bruto or "").strip()
    if not bruto:
        return {l: [] for l in LADOS}
    try:
        d = json.loads(bruto)
    except ValueError:
        m = re.search(r"\{.*\}", bruto, re.S)
        if not m:
            return {l: [] for l in LADOS}
        try:
            d = json.loads(m.group(0))
        except ValueError:
            return {l: [] for l in LADOS}
    if not isinstance(d, dict):
        return {l: [] for l in LADOS}
    saida = {}
    for lado in LADOS:
        itens = d.get(lado) or []
        saida[lado] = [
            {"lado": lado,
             "texto": (i.get("texto") or "").strip(),
             "tema_origem": (i.get("tema_origem") or "").strip().upper()}
            for i in itens
            if isinstance(i, dict) and (i.get("texto") or "").strip()
        ]
    return saida


def _medir(cand: dict, b: dict) -> dict:
    """Mede UM candidato inteiro (o conjunto de condições de uma amostra)."""
    idx = b["idx"]
    pedidos = {t["id"] for lado in LADOS for t in b["selecao"][lado]}
    conds, flags_totais = [], []
    vistos = set()
    for lado in LADOS:
        for c in cand[lado]:
            fs = validar(c, idx)
            # Um mesmo tema citado duas vezes é o modelo desobedecendo o
            # "uma condição para cada tema" — conta como flag, não é
            # silenciosamente deduplicado.
            if c["tema_origem"] in vistos:
                fs = sorted(set(fs) | {"tema_repetido"})
            vistos.add(c["tema_origem"])
            conds.append({**c, "flags": fs})
            flags_totais += fs
    cobertos = vistos & pedidos
    return {
        "condicoes": conds,
        "n_condicoes": len(conds),
        "n_flags": len(flags_totais),
        "flags": sorted(set(flags_totais)),
        "n_temas_cobertos": len(cobertos),
        "n_temas_pedidos": len(pedidos),
    }


def _chave(m: dict) -> tuple:
    """Menor é melhor.

    **PRIMÁRIA — cobertura de temas pedidos**, negada. É o análogo direto da
    "informatividade ancorada" do §3[V], e existe pela mesma razão registrada
    lá: a primeira ideia natural ("o mais curto", ou aqui "o mais limpo")
    otimiza na direção do defeito — a saída perfeitamente limpa é a lista
    vazia. A abstenção precisa ser possível sem ser premiada.

    **SECUNDÁRIA — menos flags.** Empate cai no primeiro índice, arbitrário e
    determinístico.
    """
    return (-m["n_temas_cobertos"], m["n_flags"], m["indice"])


def selecionar_candidato(candidatos: list[dict], b: dict) -> dict:
    """A escolha entre as amostras do best-of-N, e o registro do porquê.

    Diferente do §3[V] em um ponto, e ele é deliberado: lá, candidato com
    qualquer flag é ELIMINADO. Aqui a unidade com flag é a CONDIÇÃO, não o
    candidato — eliminar o conjunto inteiro por uma condição ruim jogaria
    fora quatro boas. A eliminação acontece por condição, depois da escolha.
    """
    medidos = []
    for i, cand in enumerate(candidatos):
        m = _medir(cand, b)
        m["indice"] = i
        medidos.append(m)
    vencedor = min(medidos, key=_chave)
    return {
        "indice": vencedor["indice"],
        "medida": vencedor,
        "candidatos": [{k: m[k] for k in ("indice", "n_condicoes", "n_flags",
                                          "flags", "n_temas_cobertos")}
                       for m in medidos],
    }


def prompt_retry(medida: dict) -> str:
    """O retry DIRECIONADO: diz o que reprovou, condição a condição."""
    L = ["Algumas condições foram REPROVADAS. Reescreva SOMENTE as listadas "
         "abaixo, mantendo o mesmo tema de origem e o mesmo lado. Se alguma "
         "não puder ser corrigida sem inventar, DEVOLVA-A VAZIA — saltar o "
         "tema é uma resposta correta.",
         "",
         "E a mesma PRECEDÊNCIA do anti-spoiler vale aqui: se corrigir exigiria "
         "abstrair além do que a paráfrase sustenta, SALTE o tema em vez de "
         "escolher a menos pior. Corrigir um problema criando outro não é "
         "correção.", ""]
    for c in medida["condicoes"]:
        if not c["flags"]:
            continue
        L.append(f"[{c['tema_origem']}] ({c['lado']}) → {c['texto']}")
        for f in c["flags"]:
            L.append(f"    · {f}: {_EXPLICACAO.get(f, f)}")
    L += ["", 'Responda APENAS com JSON puro, no MESMO formato de antes, '
          'contendo apenas as condições reescritas.']
    return "\n".join(L)


def _gerar_real(system: str, user: str, *, provider: str, modelo: str):
    """Uma amostra, PELO ADAPTADOR (§3[D]) — como todo caminho de LLM do
    projeto."""
    from .config import PROSA_MAX_TOKENS

    t0 = time.time()
    resp = S.resposta(system, user, modelo, provider=provider,
                      max_tokens=PROSA_MAX_TOKENS, json_mode=True)
    bruto = (resp.text if provider == "gemini"
             else resp.choices[0].message.content)
    return (bruto or ""), S.uso(resp, provider), time.time() - t0


def _somar(usos: list[dict]) -> dict:
    chaves = ("prompt_tokens", "completion_tokens",
              "cache_hit_tokens", "cache_miss_tokens")
    return {k: sum(u.get(k, 0) for u in usos) for k in chaves}


def gerar(output: dict, *, n: int = BEST_OF_N, provider: str | None = None,
          model: str | None = None, gerar=None) -> dict | None:
    """O bloco `condicoes` do JSON de resultado, pronto para gravar.

    `gerar` é o ponto de injeção dos testes: `(system, user) -> (bruto, uso,
    latencia_s)`.

    **Não existe template determinístico de fallback, e é decisão de
    desenho.** Um template de condição seria "vale a pena se você gosta de
    X" sobre o rótulo do tema — a frase vazia que a v1.9.21 gastou uma versão
    inteira para matar. Quando nada limpo sobra, a chave sai com as condições
    que sobreviveram (podendo ser NENHUMA) e `origem: "abstencao"`. **A rede
    deste estágio é o VEREDITO**, que continua sendo gerado e renderizado ao
    lado (§0, FASE 1).
    """
    b = montar_briefing(output)
    if b is None:
        return None
    user = serializar_briefing(b)

    if gerar is None:
        provider = S.provider_do_estagio(ESTAGIO, provider)
        modelo = model or S.modelo_do_estagio(ESTAGIO, provider)

        def gerar(system, msg):  # noqa: F811
            return _gerar_real(system, msg, provider=provider, modelo=modelo)
    else:
        provider, modelo = provider or "injetado", model or "injetado"

    candidatos, usos, latencias = [], [], []
    for _ in range(n):
        bruto, uso, dt = gerar(PROMPT_CONDICOES, user)
        usos.append(uso)
        latencias.append(dt)
        candidatos.append(extrair(bruto))

    escolha = selecionar_candidato(candidatos, b)
    medida = escolha["medida"]
    retry = None

    # Degrau único: se alguma condição tem flag, retry DIRECIONADO só delas.
    if medida["n_flags"]:
        bruto, uso, dt = gerar(PROMPT_CONDICOES,
                               user + "\n\n" + prompt_retry(medida))
        usos.append(uso)
        latencias.append(dt)
        corrigidas = extrair(bruto)
        por_tema = {c["tema_origem"]: c
                    for lado in LADOS for c in corrigidas[lado]}
        novas = []
        aplicadas = saltadas_no_retry = 0
        for c in medida["condicoes"]:
            if not c["flags"]:
                novas.append(c)
                continue
            nova = por_tema.get(c["tema_origem"])
            fs = validar(nova, b["idx"]) if nova else None
            # A corrigida só entra se REALMENTE melhorar (regra de §D2).
            if nova and len(fs) < len(c["flags"]):
                novas.append({**nova, "flags": fs})
                aplicadas += 1
                continue
            if not nova:
                saltadas_no_retry += 1
            # **Nada desaparece sem registro.** A condição reprovada que o
            # retry não melhorou (ou que o modelo saltou) permanece na lista
            # COM as flags dela, e a eliminação final a manda para
            # `descartadas`. Deixá-la sumir aqui apagaria a única evidência
            # de que o estágio tentou publicar algo inválido — e é
            # exatamente o tipo de ausência silenciosa que o §2.5 registrou
            # como modo de falha ("ausência tratada por omissão vira a
            # asserção que o código já tinha à mão").
            novas.append(c)
        reprovadas = sum(1 for c in medida["condicoes"] if c["flags"])
        retry = {"n_reprovadas": reprovadas,
                 "n_aplicadas": aplicadas,
                 "n_saltadas_pelo_modelo": saltadas_no_retry,
                 "n_descartadas": reprovadas - aplicadas}
        medida = {**medida, "condicoes": novas}

    # Eliminação final: condição que ainda tem flag NÃO é publicada.
    limpas = [c for c in medida["condicoes"] if not c["flags"]]
    descartadas = [{"texto": c["texto"], "tema_origem": c["tema_origem"],
                    "lado": c["lado"], "flags": c["flags"]}
                   for c in medida["condicoes"] if c["flags"]]

    idx = b["idx"]
    por_lado = {l: [] for l in LADOS}
    for c in limpas:
        t = idx.get(c["tema_origem"])
        por_lado[c["lado"]].append({
            "texto": c["texto"],
            "tema_origem": c["tema_origem"],
            "bucket_origem": t["bucket"] if t else None,
            "tema_texto": t["tema"] if t else None,
            "rotulo_forca": t["rotulo_forca"] if t else None,
        })
    # A ordem DENTRO da coluna é a da seleção (ordem publicada do bullet),
    # não a ordem em que o modelo devolveu.
    posicao = {t["id"]: i for lado in LADOS
               for i, t in enumerate(b["selecao"][lado])}
    for lado in LADOS:
        por_lado[lado].sort(key=lambda c: posicao.get(c["tema_origem"], 99))

    pedidos = {l: [t["id"] for t in b["selecao"][l]] for l in LADOS}
    escritos = {l: {c["tema_origem"] for c in por_lado[l]} for l in LADOS}
    return {
        "vale_a_pena": por_lado["vale_a_pena"],
        "talvez_evite": por_lado["talvez_evite"],
        "ordem_colunas": b["ordem_colunas"],
        "peso": b["peso"],
        "peso_meio": b["peso_meio"],
        "origem": "llm" if limpas else "abstencao",
        "temas_pedidos": pedidos,
        "temas_saltados": {l: [t for t in pedidos[l] if t not in escritos[l]]
                           for l in LADOS},
        "descartadas": descartadas,
        "retry": retry,
        "provider": provider,
        "modelo": modelo,
        "n_candidatos": len(candidatos),
        "n_chamadas": len(usos),
        "indice_escolhido": escolha["indice"],
        "candidatos": escolha["candidatos"],
        "uso": _somar(usos),
        "latencia_s": round(sum(latencias), 2),
        "spec_version": SPEC_VERSION,
    }
