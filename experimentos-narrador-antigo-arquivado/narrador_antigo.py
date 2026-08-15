"""[§D2] Narrador PRÉ-BRIEFING — ARQUIVADO na v1.9.11.

Foi o narrador de produção da v1.2.0 até a v1.9.10: recebia o JSON validado
inteiro (`_serialize_output_for_narrator`), carregava ~18 invariantes de
honestidade como INSTRUÇÃO no prompt, e pedia ao LLM que DECLARASSE o que
tinha feito (`consensos_usados`, `quantificadores_usados`,
`marcadores_perspectiva`) para que o código validasse a declaração, com
retentativa e reforço acumulado por checagem que falhasse.

**Por que foi aposentado.** A v1.9.8 substituiu o desenho: o código passa a
decidir O QUE dizer (briefing determinístico) e o narrador só verbaliza —
10 das 19 invariantes deixaram de existir como instrução viva. As v1.9.9 e
v1.9.10 corrigiram os defeitos de prosa que sobraram e acrescentaram
best-of-3 com seleção por código. **Mas nada disso estava no pipeline:**
até a v1.9.10, `cli.py` continuava chamando `narrate_output` daqui, e o
trabalho das três versões vivia só em `scripts/best_of_3.py`. A v1.9.11
integrou (`espectro24.narrador`) e este módulo saiu do caminho.

A diferença que justifica a troca, em uma linha: aqui o LLM escolhia tema,
ordem e ênfase e o código auditava a escolha; lá o código escolhe e o LLM
só escreve.

**Este módulo não é importado por `src/espectro24/`.** É código morto de
propósito — preservado para leitura e para a regressão histórica, não para
execução em produção. Como o editor arquivado (v1.9.10), ele IMPORTA
funções privadas de `espectro24.synthesize` — a maquinaria de honestidade
COMPARTILHADA (ver a lista de imports abaixo), que
continua viva lá porque `render.py`, o editor arquivado e os scripts de
diagnóstico a usam. Duplicá-la aqui criaria duas fontes de verdade para a
MESMA checagem, que é o risco que a v1.9.10 já tinha recusado.

Para rodar (não recomendado — é o código retirado, não uma opção de
configuração): `pytest experimentos-narrador-antigo-arquivado/`.
"""
from __future__ import annotations

import json
import re

from espectro24.config import BUCKETS, BUCKET_ALVO, MAX_TEMAS, PROSA_MAX_TOKENS
from espectro24.models import NarrativaResult
from espectro24.synthesize import (
    _BANDAS_QUANTIFICADOR_FRACA_PARA_FORTE,
    _REFORCO_VALIDACAO,
    _RE_PALAVRA,
    _ancoragem_de_peso_ok,
    _dividir_frases,
    _fracao_e_rotulo,
    _fracao_percentual,
    _idioma_e_pt_br,
    _marcacoes_por_bucket,
    _marcadores_validos,
    _metricas_fluencia,
    _parse_llm_json,
    _pesos_por_bucket,
    _remover_aspas,
    _resolve_call_and_model,
    _rotulo_peso_completo,
    _rotulo_quantificador,
    _strip_fences,
    _intervalo_bucket,
    _validar_prosa,
    _vocabulario_peso_ok,
)


# Reforço adicional SÓ para o narrador [D2] (v1.2.1): tamanhos de grupo vêm da
# cota de coleta, não da recepção real — anexado à retentativa combinada.
_REFORCO_PREVALENCIA = """
- Se comparou o TAMANHO dos grupos ou inferiu prevalência no público (maioria/\
minoria/grupo maior ou menor/igualmente expressivo/polarizada/dividida/\
consenso): reescreva tratando os grupos como PERSPECTIVAS, sem comparar \
tamanhos — os tamanhos vêm da cota de amostragem por faixa de nota, não da \
opinião real do público."""

# Reforço adicional SÓ para o narrador [D2] (v1.2.3) — rede de segurança do
# quantificador pré-computado: anexado à retentativa combinada.
_REFORCO_QUANTIFICADOR = """
- Se usou "quase todos" ou "praticamente todos" para algum tema sem que o \
rótulo_quantificador fornecido para aquele tema fosse exatamente esse: \
troque pelo rótulo_quantificador correto que veio no relatório — nunca \
invente um quantificador mais forte do que o fornecido."""

# Reforço adicional SÓ para o narrador [D2] (v1.4.1) — telemetria por PAR
# {quantificador, tema}: anexado à retentativa combinada quando um
# quantificador declarado é MAIS FORTE que o rótulo pré-computado do tema
# que ele mesmo citou (ou o tema citado não existe no relatório).
_REFORCO_QUANT_DECLARADO = """
- Se algum item de `quantificadores_usados` declarou uma expressão de \
frequência MAIS FORTE que o rótulo_quantificador do tema citado, ou citou um \
tema que não existe com esse nome EXATO no relatório: reescreva a prosa \
usando, para aquele tema, o rótulo_quantificador fornecido (ou um mais \
fraco) e corrija a lista para citar somente nomes de tema copiados \
literalmente do relatório. O rótulo do relatório é a autoridade — sua \
impressão de "quase todos" não é."""

# Reforço adicional SÓ para o narrador [D2] (v1.4.1) — vocabulário do peso:
# rótulo de peso vem do histograma de NOTAS, não das reviews com texto.
_REFORCO_VOCABULARIO_PESO = """
- Se você escreveu um rótulo de peso acompanhado de "reviews", "público" ou \
"espectadores" (ex.: "a grande maioria das reviews"): troque para "das \
notas". O peso vem do histograma de NOTAS do Letterboxd — todo mundo que \
avaliou o filme —, e não das reviews com texto, que são um subconjunto \
menor. As frequências de TEMA, essas sim, continuam em relação às reviews \
analisadas."""

# Reforço adicional SÓ para o narrador [D2] (v1.5.0) — marcação de
# perspectiva: anexado à retentativa combinada quando algum grupo com
# marcação exigida não teve marcador declarado, teve um trecho que não
# aparece literalmente no texto, ou (marcacao="antecipada") o marcador veio
# depois do meio do trecho sobre aquele grupo.
_REFORCO_MARCADORES = """
- Se algum grupo com marcacao_perspectiva "simples" ou "antecipada" ficou \
SEM um marcador de perspectiva dentro do trecho que fala dele (ex.: "para \
eles", "para esse grupo", "nessa leitura"), ou se `marcadores_perspectiva` \
declarou um trecho que não existe literalmente na narrativa: reescreva \
inserindo o marcador que falta, no início do trecho sobre aquele grupo \
quando a marcação for "antecipada", e registre o trecho EXATO em \
`marcadores_perspectiva`."""

# Reforço adicional SÓ para o narrador [D2] (v1.3.1) — telemetria de
# consensos: anexado à retentativa combinada quando `consensos_usados` cita
# grupo/tema inexistente no relatório recebido.
_REFORCO_CONSENSOS = """
- Se `consensos_usados` citou um grupo ("grupos_de_origem") que não é \
exatamente "negativas", "medianas" ou "positivas", ou um tema \
("temas_de_origem") que não existe, com esse nome EXATO, entre os temas do \
grupo citado no relatório recebido: corrija a lista para citar SOMENTE \
grupos e nomes de tema que existem de fato, copiados literalmente do \
relatório — ou remova o item se ele não tiver sustentação real."""

# Reforço adicional SÓ para o narrador [D2] (v1.4.0) — ancoragem de peso:
# anexado à retentativa combinada quando a prosa ignorou os rotulo_peso
# fornecidos (modo de falha esperado: o modelo reescreve a narrativa antiga,
# de pesos iguais, sem citar nenhum share).
_REFORCO_ANCORAGEM = """
- Se você NÃO ancorou cada grupo no rotulo_peso fornecido pelo relatório: \
reescreva o MOVIMENTO 3 apresentando cada grupo com o seu rotulo_peso (e o \
percentual), começando pela perspectiva de MAIOR peso e dando mais espaço a \
ela. Não trate os três grupos como se pesassem o mesmo — o relatório diz \
quanto cada um pesa de verdade."""





_NARRADOR_PARTE_1 = """\
Você recebe um RELATÓRIO DE RECEPÇÃO já validado de um filme: três grupos de \
reviews separados por faixa de nota (negativas, medianas, positivas), cada um \
com seus temas, frequências aproximadas e uma observação; e, quando \
disponível, uma FICHA TÉCNICA do filme (sinopse oficial, diretor, gênero, \
ano, duração — fonte: TMDB). Sua tarefa é reescrever esse material como um \
texto corrido e envolvente, em TRÊS MOVIMENTOS, SEM subtítulos ou marcações \
entre eles (a divisão é para você se organizar, não para aparecer no texto), \
NESTA ORDEM:

MOVIMENTO 1 — O FILME (2-3 frases; SÓ escreva este movimento SE houver FICHA \
TÉCNICA no relatório — sem ficha, comece direto no MOVIMENTO 2): apresente a \
premissa do filme a partir da `sinopse_oficial` da ficha — pode condensá-la, \
mas é PROIBIDO expandi-la com qualquer conhecimento externo sobre o filme, \
elenco, direção ou produção que não esteja na ficha fornecida. Se a \
`sinopse_oficial` parecer revelar algo além da premissa inicial do filme, \
use só a parte que é premissa e ignore o resto (a ficha NÃO tem passe livre \
sobre a regra de anti-spoiler abaixo). Mencione diretor, gênero e ano; \
duração só se for relevante para o que os dois movimentos seguintes vão \
dizer (ex.: filme muito longo/curto vira tema na experiência).

MOVIMENTO 2 — A EXPERIÊNCIA (3-5 frases): descreva como é assistir ao filme \
usando APENAS propriedades DESCRITIVAS da experiência (ritmo, tom, \
atmosfera, intensidade, estrutura, ambientação, nível de violência, \
ambiguidade, densidade) em que os grupos CONCORDAM no NÚCLEO FACTUAL, mesmo \
divergindo na avaliação. Tom NEUTRO, SEM valência — este movimento \
descreve, não julga; gostar ou não gostar fica para o MOVIMENTO 3. Uma \
propriedade só entra neste movimento se passar nos TRÊS critérios abaixo, \
TODOS obrigatórios (v1.3.1 — reescrito após um defeito real observado):

a. CRITÉRIO DE CATEGORIA: só propriedades DESCRITIVAS. É PROIBIDO qualquer \
juízo de QUALIDADE (atuações boas/ruins, roteiro inteligente/fraco, direção \
competente/questionável, elenco talentoso/fraco) — julgamento de qualidade \
é sempre disputado entre quem gostou e quem não gostou, e pertence ao \
MOVIMENTO 3, NUNCA a este.
b. CRITÉRIO DE PRESENÇA: a propriedade precisa derivar de temas de PELO \
MENOS DOIS grupos, com o mesmo núcleo factual — a valência pode divergir \
("lento e tedioso" num grupo + "lento e deliberado" noutro = consenso \
factual "ritmo lento"; a avaliação de cada grupo sobre esse ritmo é coisa \
diferente e não entra aqui).
c. CRITÉRIO DE NÃO-CONTRADIÇÃO: se QUALQUER grupo contradiz o núcleo \
factual (não só diverge na avaliação, mas nega o fato em si), a propriedade \
está desqualificada — não entra no MOVIMENTO 2 de jeito nenhum.

EXEMPLO POSITIVO (os três critérios satisfeitos): as reviews negativas \
chamam o ritmo de "lento e tedioso", as positivas de "lento e deliberado" \
— ambos descrevem RITMO (categoria descritiva, critério a), os dois grupos \
concordam no núcleo "lento" (critério b), nenhum grupo nega isso (critério \
c) → consenso válido para o MOVIMENTO 2: "ritmo lento e contemplativo".

EXEMPLO NEGATIVO (falha real observada, v1.3.0 — caso de "the-invite-2026"): \
as reviews positivas elogiam "atuações marcantes" e "roteiro inteligente"; \
as negativas têm os temas "atuações e direção questionáveis" e "roteiro \
fraco". Isso NÃO é consenso: é uma propriedade AVALIATIVA (qualidade de \
atuação, qualidade de roteiro — falha o critério a) E os grupos se \
contradizem diretamente sobre ela (falha o critério c também). O correto é \
NÃO mencionar qualidade de atuação/roteiro no MOVIMENTO 2 — essa disputa \
pertence ao MOVIMENTO 3, atribuída a cada grupo separadamente.

É PROIBIDO importar qualquer informação que não venha dos temas validados \
dos três grupos.

OMISSÃO AUTORIZADA (v1.4.1 — leia isto antes de escrever o movimento): se \
MENOS DE DUAS propriedades passarem nos três critérios ao mesmo tempo, este \
movimento deve ser CURTO (1 frase) ou AUSENTE — e a narrativa passa direto \
ao MOVIMENTO 3. OMITIR É O COMPORTAMENTO CORRETO, não uma falha: não há cota \
de frases a cumprir aqui, e um filme cujos temas descritivos são poucos \
simplesmente não tem um MOVIMENTO 2. Preencher o espaço com juízo de \
qualidade suavizado ("estilo visual eficaz", "abordagem arrojada", \
"atuações competentes", "roteiro habilidoso") é PIOR do que não ter o \
movimento — é o defeito que o critério (a) proíbe, disfarçado de descrição \
por um advérbio de hesitação. Quando o movimento é omitido, \
`consensos_usados` vem como lista VAZIA ([]) — isso é resultado esperado, \
não erro. Para \
CADA propriedade usada no MOVIMENTO 2, registre em `consensos_usados` (ver \
formato de saída) a propriedade, os grupos de onde ela veio e os nomes \
EXATOS dos temas (copiados literalmente do relatório) que a sustentam — \
esse registro é o artefato de revisão humana que confirma que o consenso é \
real, não inventado.

MOVIMENTO 3 — O CONTRASTE (enxuto — a interface já exibe as barras de \
frequência tema a tema, então aqui priorize os 2-3 temas MAIS FORTES de \
cada grupo, não a cobertura completa dos 6 possíveis): as perspectivas dos \
três grupos — quem não gostou, quem ficou no meio, quem gostou — sobre o \
filme. Neste movimento (e em qualquer lugar do texto que fale de grupos) \
valem as invariantes abaixo, TODAS ainda em vigor:

a. PAPEL: o texto inteiro é para alguém que está DECIDINDO se assiste ao \
filme e que AINDA NÃO ASSISTIU.
b. FIDELIDADE: toda afirmação deve derivar da ficha técnica e/ou dos temas e \
números recebidos. É PROIBIDO adicionar fatos, opiniões próprias, ou \
qualquer contexto externo sobre o filme, elenco, direção ou produção que \
não esteja no relatório. Se não está nos dados, não existe.
"""

_REGRA_C_SEM_DISTRIBUICAO = """\
c. TAMANHO DOS GRUPOS — REGRA CRÍTICA: os três grupos NÃO têm o tamanho da \
opinião real do público. O tamanho de cada grupo é fixado pelo MÉTODO DE \
COLETA (uma cota fixa por faixa de nota), não pela quantidade de pessoas que \
pensam assim — as medianas, por exemplo, serão sempre o menor grupo por \
construção, em todo filme. Portanto é PROIBIDO comparar tamanhos entre grupos \
ou inferir prevalência global: NADA de "a maioria dos espectadores", "a \
maioria do público", "grupo maior", "grupo menor", "minoria", "igualmente \
expressivo", "recepção polarizada", "opiniões divididas", "consenso" ou \
qualquer equivalente. Trate cada grupo como uma PERSPECTIVA, não como uma \
fatia quantificada do público: apresente-os como "entre quem não gostou...", \
"já entre quem amou...", "para quem ficou no meio-termo...".
"""

# v1.9.0 — o literal da cota vira DERIVADO de BUCKET_ALVO. Não é mudança de
# regra: a cota passou de 50/20/30 para 40/40/40 nesta versão, e deixar o
# número antigo escrito no prompt entregaria ao LLM um dado falso sobre o
# próprio pipeline. Mesma correção feita no disclaimer de `render.py`.
_COTAS_TXT = "/".join(str(BUCKET_ALVO[n]) for n in BUCKET_ALVO)

_REGRA_C_COM_DISTRIBUICAO = f"""\
c. PESO REAL DE CADA GRUPO — REGRA CRÍTICA (a distribuição está disponível \
neste relatório): você recebeu a DISTRIBUIÇÃO REAL das notas do filme, vinda \
do histograma público — quantas pessoas deram cada nota. Isso é um dado \
diferente do tamanho dos grupos de reviews analisadas ({_COTAS_TXT}), que é \
apenas a COTA DE COLETA e continua NÃO significando prevalência. Regras:
- ANCORAGEM OBRIGATÓRIA: cada grupo DEVE ser apresentado, na primeira vez que \
aparecer no MOVIMENTO 3, com o rotulo_peso que veio no relatório para ele \
(ex.: "a grande maioria das notas (~79%)"). É PROIBIDO usar um rótulo MAIS \
FORTE do que o fornecido; um MAIS FRACO é permitido se a fluência pedir — \
nunca o oposto. Você NÃO calcula nem escolhe esse rótulo: ele é dado.
- ABERTURA OBRIGATÓRIA: o MOVIMENTO 3 começa pela perspectiva de MAIOR peso. \
Esta regra tem precedência sobre a liberdade de ordem da regra (e).
- ÊNFASE PROPORCIONAL: dê aproximadamente mais espaço ao grupo de maior peso \
e menos ao de menor peso — um filme amplamente amado não pode soar dividido, \
e um amplamente rejeitado não pode soar morno.
- RESPEITO À MINORIA: a perspectiva minoritária é apresentada COMO \
minoritária, mas SEM desdém, ironia ou insinuação de que quem pensa assim \
está errado. Menos espaço, mesma seriedade analítica: quem procura saber se \
vai gostar precisa entender o que incomodou essa parcela.
- VOCABULÁRIO OBRIGATÓRIO — NOTAS, NUNCA REVIEWS (v1.4.1): o rotulo_peso vem \
do histograma de NOTAS do Letterboxd, ou seja, de TODO MUNDO que avaliou o \
filme; os temas vêm das REVIEWS COM TEXTO, um subconjunto bem menor. São \
duas populações diferentes. Portanto, ao expressar peso, é OBRIGATÓRIO \
escrever "das notas" ("a grande maioria das notas (~79%)") e é PROIBIDO \
escrever "das reviews", "dos espectadores" ou "do público" — o histograma \
não diz nada sobre quem escreveu review nem sobre quem assistiu sem avaliar. \
As frequências de TEMA seguem no vocabulário oposto (regra d): sempre em \
relação às reviews analisadas daquele grupo. Os dois vocabulários nunca se \
misturam.
- Continua PROIBIDO inventar um número-síntese do filme (nota média, score, \
"X de 10", "nota N"): os shares por faixa são a ÚNICA quantificação \
permitida, e são três números, nunca um só.

MARCAÇÃO DE PERSPECTIVA (v1.5.0 — motivada pela regra de REGISTRO abaixo): \
ao reduzir os verbos de reporte, a fala de um grupo minoritário pode soar \
como fato do narrador — porque ela chega depois de o texto já ter \
estabelecido a leitura dominante. Cada grupo do relatório vem com uma \
`marcacao_perspectiva` PRÉ-COMPUTADA (nenhuma/simples/antecipada, a partir \
do share_real — você NÃO calcula nem escolhe esse valor):
- TODO trecho que falar de um grupo precisa conter ao menos uma ANCORAGEM \
de perspectiva para ele; para o grupo DOMINANTE, o próprio rótulo de peso \
já cumpre esse papel ("quem gostou é a grande maioria das notas (~74%)" já \
ancora — nenhum marcador extra é exigido).
- marcacao_perspectiva="simples": além da abertura, inclua ao menos UM \
marcador de perspectiva DENTRO do trecho que fala desse grupo (ex.: "para \
eles", "para esse grupo", "nessa leitura", "quem está nessa faixa").
- marcacao_perspectiva="antecipada": o marcador interno precisa vir ANTES \
da primeira afirmação substantiva sobre esse grupo, não no fim do trecho.
- Um marcador de perspectiva NÃO é um verbo de reporte e NÃO conta para o \
limite da regra (f) de REGISTRO: "para eles o humor é previsível" é \
marcação; "eles apontam que o humor é previsível" é reporte e continua \
limitado.
- É PROIBIDO um marcador com carga depreciativa ("apenas para eles", "só \
para esses poucos") — a perspectiva minoritária continua apresentada com \
respeito (mesma RESPEITO À MINORIA acima).
Para CADA marcador de perspectiva que você usar, registre em \
`marcadores_perspectiva` (ver formato de saída) o grupo e o TRECHO EXATO, \
copiado literalmente da narrativa, onde ele aparece.

"""

_NARRADOR_PARTE_2 = """\
d. PROPORÇÕES (só DENTRO de um grupo): proporções são permitidas APENAS \
internamente a um grupo e SEMPRE ancoradas ao denominador daquele grupo. \
NUNCA uma proporção que compare grupos ou fale do público como um todo.
QUANTIFICADOR PRÉ-COMPUTADO (obrigatório, v1.2.3): cada tema do relatório já \
vem com um rótulo_quantificador calculado pelo CÓDIGO a partir da fração \
real de menções — você NÃO calcula nem escolhe o quantificador sozinho. Ao \
expressar a frequência de um tema em prosa, USE o rótulo_quantificador \
fornecido para aquele tema (sinônimos de mesma força são permitidos: "a \
maioria" ~ "mais da metade"; "muitos" ~ "boa parte"; "alguns" ~ "uma \
parte"). É PROIBIDO usar um quantificador MAIS FORTE do que o fornecido. Um \
quantificador MAIS FRACO é permitido se a fluência do texto pedir — nunca \
o oposto. Escala de força, do mais fraco ao mais forte: poucos < \
alguns/uma parte < muitos/boa parte < cerca de metade < a maioria/mais da \
metade < quase todos/praticamente todos.
DECLARAÇÃO OBRIGATÓRIA DOS QUANTIFICADORES (v1.4.1): para CADA expressão de \
frequência que você usar na prosa ao falar de um tema, registre um item em \
`quantificadores_usados` (ver formato de saída) com o quantificador EXATO \
que você escreveu e o NOME EXATO do tema (copiado literalmente do relatório) \
de onde aquela frequência vem — um item por expressão usada. Antes de \
declarar, confira o par contra o relatório: se o quantificador que você \
escreveu for mais forte que o rótulo_quantificador daquele tema, corrija a \
PROSA (não o registro). Se você não usar nenhum quantificador de tema, a \
lista vem vazia.
e. ESTRUTURA: a divisão em três grupos (quem não gostou / quem ficou no meio \
/ quem gostou) deve permanecer legível na prosa do MOVIMENTO 3, em qualquer \
ordem que sirva à narrativa.
f. ESCOPO: cada afirmação sobre um grupo é atribuída ao SEU grupo ("as \
reviews negativas apontam...", "quem deu notas altas destaca..."). É \
PROIBIDO generalizar para "os críticos", "a maioria" (do filme todo) ou "o \
consenso".
g. ANTI-SPOILER: em QUALQUER movimento (incluindo o 1, com a sinopse \
oficial), é PROIBIDO mencionar eventos de trama, personagens específicos ou \
desfechos, mesmo que a sinopse ou algum tema tangencie isso (defesa em \
profundidade — a camada anterior já filtra os temas, você reforça, e a \
sinopse oficial é tratada com a mesma cautela).
h. FORMA: português do Brasil, SEM aspas de citação, SEM subtítulos ou \
rótulos dos movimentos no texto final, entre 250 e 400 palavras ao todo.

NOTA SOBRE ESTILO (v1.6.0): não se preocupe com ritmo, variação de frase ou \
elegância da prosa. Um ESTÁGIO SEGUINTE de edição cuida disso, e ele NÃO \
pode alterar nenhum número, rótulo ou atribuição que você escrever. Sua \
única responsabilidade é dizer a verdade com a estrutura acima — escreva de \
forma clara e gramaticalmente correta, e deixe o polimento para depois.

Responda APENAS com JSON puro no formato: {"narrativa": "<seu texto>", \
"consensos_usados": [{"propriedade": "<nome curto da propriedade \
descritiva>", "grupos_de_origem": ["<negativas|medianas|positivas>", ...], \
"temas_de_origem": ["<nome EXATO do tema, copiado do relatório>", ...]}], \
"quantificadores_usados": [{"quantificador": "<a expressão de frequência \
EXATA que você escreveu na prosa>", "tema": "<nome EXATO do tema, copiado \
do relatório, de onde ela vem>"}], "marcadores_perspectiva": [{"grupo": \
"<negativas|medianas|positivas>", "trecho": "<o trecho EXATO da narrativa, \
copiado literalmente, onde o marcador de perspectiva desse grupo \
aparece>"}]}. `consensos_usados` pode ser `[]` se o MOVIMENTO 2 não usou \
nenhuma propriedade consensual (ver OMISSÃO AUTORIZADA); \
`quantificadores_usados` pode ser `[]` se a prosa não quantificou nenhum \
tema; `marcadores_perspectiva` pode ser `[]` quando nenhum grupo do \
relatório exige marcação de perspectiva (regra específica, presente só \
quando o relatório trouxer distribuição real de notas)."""

# Prompt histórico (sem distribuição) — mantido como CONSTANTE com o mesmo
# nome e o mesmo conteúdo byte-a-byte da v1.3.1, para que o fallback seja
# literalmente o comportamento anterior, não uma reescrita parecida.
NARRATOR_SYSTEM_PROMPT = (
    _NARRADOR_PARTE_1 + _REGRA_C_SEM_DISTRIBUICAO + _NARRADOR_PARTE_2
)

NARRATOR_SYSTEM_PROMPT_COM_DISTRIBUICAO = (
    _NARRADOR_PARTE_1 + _REGRA_C_COM_DISTRIBUICAO + _NARRADOR_PARTE_2
)

def build_narrator_prompt(com_distribuicao: bool) -> str:
    """Escolhe a variante da regra (c) do §D2 (v1.4.0).

    `com_distribuicao=False` devolve EXATAMENTE o prompt da v1.3.1 — o
    fallback não é uma aproximação, é o texto anterior. A escolha é feita
    pelo CÓDIGO a partir da presença do dado, nunca pelo LLM.
    """
    return (NARRATOR_SYSTEM_PROMPT_COM_DISTRIBUICAO if com_distribuicao
            else NARRATOR_SYSTEM_PROMPT)

def _algum_tema_tem_fracao_forte(output: dict, limiar_pct: int = 80) -> bool:
    """True se QUALQUER tema de QUALQUER bucket do filme tem fração >= limiar
    — usado pela rede de segurança (v1.2.3) para saber se "quase todos"/
    "praticamente todos" tem lastro em algum lugar do relatório."""
    for b in output.get("buckets", []):
        for t in b.get("temas") or []:
            pct, _ = _fracao_e_rotulo(t)
            if pct >= limiar_pct:
                return True
    return False

def _tem_quantificador_forte_no_texto(texto: str) -> bool:
    t = texto.lower()
    return "quase todos" in t or "praticamente todos" in t

# Expressão declarada -> posição na escala de força do prompt (0 = mais
# fraco). As chaves cobrem os sinônimos que o próprio prompt autoriza
# ("a maioria" ~ "mais da metade"; "muitos" ~ "boa parte"; "alguns" ~ "uma
# parte") mais as flexões de gênero, que aparecem naturalmente em pt-BR.
_FORCA_QUANTIFICADOR = {
    "poucos": 0, "poucas": 0,
    "alguns": 1, "algumas": 1, "uma parte": 1, "parte dos": 1, "parte das": 1,
    "muitos": 2, "muitas": 2, "boa parte": 2,
    "cerca de metade": 3, "aproximadamente metade": 3, "metade": 3,
    "a maioria": 4, "maioria": 4, "mais da metade": 4,
    "quase todos": 5, "quase todas": 5,
    "praticamente todos": 5, "praticamente todas": 5,
}

# Ordem canônica dos rótulos pré-computados = a própria escala de força.
_ORDEM_ROTULO_QUANTIFICADOR = [r for r, _, _, _ in
                               _BANDAS_QUANTIFICADOR_FRACA_PARA_FORTE]

def _forca_declarada(quantificador: str) -> int | None:
    """Força (0-5) da expressão declarada pelo narrador, ou None se ela não
    for reconhecível.

    Casa por SUBSTRING, testando as chaves mais longas primeiro — assim
    "quase todos os elogios" resolve para "quase todos", e "mais da metade"
    não é confundido com "metade". Expressão irreconhecível devolve None e a
    checagem a ignora: heurística deliberadamente permissiva, como as demais
    redes de segurança do §D2 (limitação documentada na SPEC).
    """
    q = quantificador.lower()
    for chave in sorted(_FORCA_QUANTIFICADOR, key=len, reverse=True):
        if chave in q:
            return _FORCA_QUANTIFICADOR[chave]
    return None

def _rotulos_por_tema(output: dict) -> dict[str, int]:
    """{nome do tema: força do rótulo pré-computado}.

    Tema com o MESMO nome em mais de um grupo (frações diferentes) resolve
    para a força MAIS ALTA entre eles — o par declarado não diz de qual grupo
    veio, e na ambiguidade a checagem prefere não flaggar uma prosa correta.
    """
    forcas: dict[str, int] = {}
    for b in output.get("buckets", []):
        for t in b.get("temas") or []:
            nome = str(t.get("tema", ""))
            _pct, rotulo = _fracao_e_rotulo(t)
            forca = _ORDEM_ROTULO_QUANTIFICADOR.index(rotulo)
            forcas[nome] = max(forcas.get(nome, -1), forca)
    return forcas

def _quantificadores_validos(quantificadores: list, output: dict) -> bool:
    """True se todo par {quantificador, tema} declarado cita um tema REAL do
    filme e usa uma expressão que NÃO é mais forte que o rótulo pré-computado
    daquele tema. Lista vazia é vacuamente válida (a prosa pode não
    quantificar tema nenhum)."""
    forcas = _rotulos_por_tema(output)
    for q in quantificadores or []:
        if not isinstance(q, dict):
            return False
        tema = str(q.get("tema", ""))
        if tema not in forcas:
            return False
        declarada = _forca_declarada(str(q.get("quantificador", "")))
        if declarada is not None and declarada > forcas[tema]:
            return False
    return True

def _normalizar_quantificadores(quantificadores: list) -> list[dict]:
    out = []
    for q in quantificadores or []:
        if not isinstance(q, dict):
            continue
        out.append({
            "quantificador": str(q.get("quantificador", "")),
            "tema": str(q.get("tema", "")),
        })
    return out

def _serialize_output_for_narrator(output: dict) -> str:
    """Serialização COMPACTA do JSON validado para o narrador (§D2).

    Lê apenas campos seguros de `output` (temas/números/observacoes) — nunca
    reviews brutas (que não existem em `output`). Buckets `sem_analise` entram
    com a contagem e o modo, para que a prosa reflita a escassez sem inventar.

    v1.2.3: cada tema carrega `fracao`/`rótulo_quantificador` PRÉ-COMPUTADOS
    pelo código (`_fracao_e_rotulo`) — o narrador só usa o rótulo dado, nunca
    calcula nem escolhe (ver regra (d) do prompt e a motivação no changelog).

    v1.3.0: quando `output['ficha']` existe (TMDB — ver ficha.py), uma seção
    FICHA TÉCNICA precede os grupos, fonte exclusiva do MOVIMENTO 1 do
    prompt. Ficha ausente (busca falhou/pulada) -> a seção some inteira e o
    prompt já instrui o narrador a pular o MOVIMENTO 1 nesse caso.

    v1.4.0: quando há distribuição real, um bloco DISTRIBUIÇÃO REAL abre o
    relatório e cada GRUPO passa a carregar seu `rotulo_peso` pré-computado.
    Sem distribuição, nada disso aparece e o relatório é o da v1.3.1 — o
    silêncio é o próprio fallback.
    """
    linhas = [
        "RELATÓRIO DE RECEPÇÃO (dados já validados; use SOMENTE isto):",
        f"Total de reviews observadas na coleta do filme: "
        f"{output.get('total_reviews_observadas', 0)}",
        "",
    ]
    ficha = output.get("ficha")
    if ficha:
        linhas.append(
            "FICHA TÉCNICA (TMDB — fonte EXCLUSIVA do MOVIMENTO 1; "
            "sinopse_oficial é material de divulgação curado, PROIBIDO "
            "expandir com conhecimento externo):")
        linhas.append(f"  titulo: {ficha.get('titulo')}")
        linhas.append(f"  ano: {ficha.get('ano')}")
        linhas.append(f"  diretor: {ficha.get('diretor')}")
        linhas.append(f"  generos: {', '.join(ficha.get('generos') or [])}")
        linhas.append(f"  duracao_min: {ficha.get('duracao_min')}")
        linhas.append(f"  sinopse_oficial: {ficha.get('sinopse_oficial')}")
        linhas.append("")

    pesos = _pesos_por_bucket(output)
    marcacoes = _marcacoes_por_bucket(pesos)
    if pesos:
        distrib = output.get("distribuicao") or {}
        linhas.append(
            "DISTRIBUIÇÃO REAL DAS NOTAS (histograma público do Letterboxd — "
            f"{distrib.get('n_notas_total', 0)} notas no total). Este é o PESO "
            "de cada faixa na recepção real, e é diferente do número de "
            "reviews analisadas (que é cota de coleta). Use o rotulo_peso "
            "abaixo — não calcule nem escolha outro:")
        for nome, (pct, _rot) in pesos.items():
            linhas.append(
                f'  {nome}: share_real {pct}% · rotulo_peso: '
                f'"{_rotulo_peso_completo(pct)}" · marcacao_perspectiva: '
                f'"{marcacoes[nome]}"')
        linhas.append("")

    rotulo = {"negativas": "NÃO GOSTARAM", "medianas": "FICARAM NO MEIO",
              "positivas": "GOSTARAM"}
    for b in output.get("buckets", []):
        nome = b.get("bucket", "?")
        intervalo = _intervalo_bucket(nome) if nome in BUCKETS else ""
        peso_txt = ""
        if nome in pesos:
            peso_txt = (f' · rotulo_peso: "{_rotulo_peso_completo(pesos[nome][0])}"'
                        f' · marcacao_perspectiva: "{marcacoes[nome]}"')
        linhas.append(
            f"GRUPO {nome.upper()} ({rotulo.get(nome, '')}, {intervalo}) — "
            f"{b.get('n_validas', 0)} reviews analisadas · "
            f"modo={b.get('modo')}{peso_txt}:")
        obs = b.get("observacao_geral", "")
        if obs:
            linhas.append(f"  observação do grupo: {obs}")
        temas = b.get("temas") or []
        if temas:
            linhas.append("  temas (por frequência decrescente):")
            for t in temas:
                pct, rot_quant = _fracao_e_rotulo(t)
                linhas.append(
                    f"    - {t.get('tema')} — ~{t.get('mencoes_aproximadas')} de "
                    f"{t.get('n_reviews_analisadas')} reviews "
                    f"(fracao: {pct}%, rótulo_quantificador: \"{rot_quant}\"). "
                    f"ex.: {t.get('exemplo_parafraseado')}")
        else:
            linhas.append("  (sem temas — poucas reviews neste grupo)")
        linhas.append("")
    return "\n".join(linhas)

_GRUPOS_VALIDOS = {"negativas", "medianas", "positivas"}

def _temas_por_grupo(output: dict) -> dict[str, set[str]]:
    return {
        b.get("bucket"): {t.get("tema") for t in (b.get("temas") or [])}
        for b in output.get("buckets", [])
    }

def _consensos_validos(consensos: list, output: dict) -> bool:
    """True se todo item de `consensos_usados` cita SOMENTE grupos válidos
    (negativas/medianas/positivas presentes no relatório) e temas que
    existem, com o nome EXATO, em algum dos grupos citados naquele item.
    Lista vazia é vacuamente válida (MOVIMENTO 2 pode não usar nenhuma)."""
    temas_por_grupo = _temas_por_grupo(output)
    for c in consensos or []:
        if not isinstance(c, dict):
            return False
        grupos = c.get("grupos_de_origem")
        temas = c.get("temas_de_origem")
        if not isinstance(grupos, list) or not isinstance(temas, list):
            return False
        if not all(g in _GRUPOS_VALIDOS and g in temas_por_grupo for g in grupos):
            return False
        temas_disponiveis = set()
        for g in grupos:
            temas_disponiveis |= temas_por_grupo.get(g, set())
        if not all(t in temas_disponiveis for t in temas):
            return False
    return True

def _normalizar_consensos(consensos: list) -> list[dict]:
    out = []
    for c in consensos or []:
        if not isinstance(c, dict):
            continue
        out.append({
            "propriedade": str(c.get("propriedade", "")),
            "grupos_de_origem": [str(g) for g in (c.get("grupos_de_origem") or [])],
            "temas_de_origem": [str(t) for t in (c.get("temas_de_origem") or [])],
        })
    return out

def _normalizar_marcadores(marcadores: list) -> list[dict]:
    out = []
    for m in marcadores or []:
        if not isinstance(m, dict):
            continue
        out.append({
            "grupo": str(m.get("grupo", "")),
            "trecho": str(m.get("trecho", "")),
        })
    return out

def narrate_output(output: dict, client_call=None, model: str | None = None,
                   provider: str | None = None) -> "NarrativaResult":
    """[D2] Gera a narrativa em prosa a partir do JSON validado `output`.

    UMA chamada LLM para o filme inteiro (não por bucket), mesmo provider/modelo
    da síntese. Parsing defensivo do JSON `{"narrativa": ...}` com 1 retentativa;
    validações de prosa (idioma/aspas/escopo) com 1 retentativa combinada, nos
    mesmos moldes do §D. A assinatura da spec é `-> str` (o texto); aqui
    retornamos `NarrativaResult` para carregar também a telemetria das flags.
    Rede de segurança do quantificador (v1.2.3): mesmo com o rótulo
    pré-computado no relatório, checa se a prosa usou "quase todos"/
    "praticamente todos" sem QUALQUER tema do filme ter fração >= 80% — o
    único modo de falha observado (ver changelog v1.2.3). Deliberadamente
    restrita a esse quantificador mais forte; não cobre uso indevido dos
    demais rótulos.

    v1.4.1 — telemetria POR PAR: a checagem acima é de nível de BUCKET e não
    pegou a 3ª reincidência do modo de falha ("quase todos" para um tema de
    67%, enquanto outro tema do mesmo grupo tinha 83% e dava lastro). O
    narrador passa a DECLARAR `quantificadores_usados` — {quantificador,
    tema} — e o código confere par a par contra o rótulo pré-computado
    daquele tema; par inflado ou tema inexistente => retentativa com reforço
    e, se persistir, a mesma flag `quantificador_suspeito`. Também v1.4.1: o
    vocabulário do peso ("das notas", nunca "das reviews"/"do público"/"dos
    espectadores"), com flag própria `vocabulario_peso_suspeito`.
    """

    call, model = _resolve_call_and_model(client_call, model, provider)
    # v1.4.0: a presença do dado — não uma flag de configuração — decide qual
    # variante da regra (c) vale. Sem distribuição, tudo abaixo degrada
    # sozinho para o comportamento da v1.3.1.
    pesos = _pesos_por_bucket(output)
    com_distribuicao = bool(pesos)
    # v1.5.0: marcação de perspectiva também depende do dado real — vazio
    # sem distribuição, mesmo padrão de `pesos`.
    marcacoes = _marcacoes_por_bucket(pesos)
    system = build_narrator_prompt(com_distribuicao)
    user = _serialize_output_for_narrator(output)
    tem_tema_forte = _algum_tema_tem_fracao_forte(output)

    def _uma_chamada(sys_prompt: str) -> tuple[str, list, list, list] | None:
        raw = call(sys_prompt, user, model)
        try:
            data = _parse_llm_json(raw)
        except (ValueError, json.JSONDecodeError):
            return None
        consensos = data.get("consensos_usados")
        if not isinstance(consensos, list):
            consensos = []
        quantificadores = data.get("quantificadores_usados")
        if not isinstance(quantificadores, list):
            quantificadores = []
        marcadores = data.get("marcadores_perspectiva")
        if not isinstance(marcadores, list):
            marcadores = []
        return str(data.get("narrativa", "")), consensos, quantificadores, marcadores

    def _quantificador_bucket_ok(texto: str) -> bool:
        """Rede de segurança da v1.2.3 (nível de BUCKET) — mantida em vigor."""
        return not (_tem_quantificador_forte_no_texto(texto) and not tem_tema_forte)

    # chamada + 1 retentativa de JSON inválido
    resultado = _uma_chamada(system)
    if resultado is None:
        resultado = _uma_chamada(system)
    if resultado is None:
        return NarrativaResult(texto="", falhou=True,
                               idioma_invalido=False, escopo_suspeito=False)

    def _ancoragem_ok(texto: str) -> bool:
        # Sem distribuição não há o que ancorar: vacuamente OK.
        return _ancoragem_de_peso_ok(texto, pesos) if com_distribuicao else True

    prosa, consensos_brutos, quantificadores_brutos, marcadores_brutos = resultado
    texto, idioma_ok, escopo_ok, prevalencia_ok, aspas_removidas = _validar_prosa(
        prosa, com_distribuicao)
    quant_bucket_ok = _quantificador_bucket_ok(texto)
    quant_declarado_ok = _quantificadores_validos(quantificadores_brutos, output)
    consensos_ok = _consensos_validos(consensos_brutos, output)
    ancoragem_ok = _ancoragem_ok(texto)
    vocabulario_ok = _vocabulario_peso_ok(texto, pesos)
    marcadores_ok = _marcadores_validos(marcadores_brutos, texto, marcacoes, pesos)
    # v1.6.0: métricas viram DIAGNÓSTICO — calculadas e persistidas, mas sem
    # gatilho de retentativa (ver nota em `_metricas_fluencia`).
    metricas = _metricas_fluencia(texto)

    # 1 retentativa combinada se idioma, escopo, prevalência, quantificador
    # (nível de bucket, v1.2.3, ou por par declarado, v1.4.1), consensos_usados
    # (v1.3.1), ancoragem de peso (v1.4.0), vocabulário do peso (v1.4.1) ou
    # marcadores de perspectiva (v1.5.0) falharem. Fluência saiu desta lista
    # na v1.6.0 — é responsabilidade do editor (§E2), não do narrador.
    if not idioma_ok or not escopo_ok or not prevalencia_ok \
            or not quant_bucket_ok or not quant_declarado_ok \
            or not consensos_ok or not ancoragem_ok or not vocabulario_ok \
            or not marcadores_ok:
        reforco = _REFORCO_VALIDACAO + _REFORCO_QUANTIFICADOR
        # o reforço de prevalência PROÍBE falar de peso — anexá-lo com
        # distribuição presente contradiria a regra (c) invertida.
        if not com_distribuicao:
            reforco += _REFORCO_PREVALENCIA
        if not quant_declarado_ok:
            reforco += _REFORCO_QUANT_DECLARADO
        if not consensos_ok:
            reforco += _REFORCO_CONSENSOS
        if not ancoragem_ok:
            reforco += _REFORCO_ANCORAGEM
        if not vocabulario_ok:
            reforco += _REFORCO_VOCABULARIO_PESO
        if not marcadores_ok:
            reforco += _REFORCO_MARCADORES
        retry = _uma_chamada(system + reforco)
        if retry is not None:
            prosa2, consensos2, quantificadores2, marcadores2 = retry
            t2, i2, e2, p2, a2 = _validar_prosa(prosa2, com_distribuicao)
            texto, idioma_ok, escopo_ok, prevalencia_ok = t2, i2, e2, p2
            aspas_removidas = aspas_removidas or a2
            quant_bucket_ok = _quantificador_bucket_ok(texto)
            quantificadores_brutos = quantificadores2
            quant_declarado_ok = _quantificadores_validos(
                quantificadores_brutos, output)
            consensos_brutos = consensos2
            consensos_ok = _consensos_validos(consensos_brutos, output)
            ancoragem_ok = _ancoragem_ok(texto)
            vocabulario_ok = _vocabulario_peso_ok(texto, pesos)
            marcadores_brutos = marcadores2
            marcadores_ok = _marcadores_validos(marcadores_brutos, texto, marcacoes, pesos)
            metricas = _metricas_fluencia(texto)

    return NarrativaResult(
        texto=texto,
        idioma_invalido=not idioma_ok,
        escopo_suspeito=not escopo_ok,
        prevalencia_suspeita=not prevalencia_ok,
        # v1.4.1: a MESMA flag passa a ser alimentada pelas DUAS checagens —
        # a de bucket (v1.2.3) e a por par declarado (v1.4.1).
        quantificador_suspeito=not (quant_bucket_ok and quant_declarado_ok),
        aspas_removidas=aspas_removidas,
        consensos_usados=_normalizar_consensos(consensos_brutos),
        consenso_suspeito=not consensos_ok,
        peso_nao_ancorado=not ancoragem_ok,
        quantificadores_usados=_normalizar_quantificadores(quantificadores_brutos),
        vocabulario_peso_suspeito=not vocabulario_ok,
        marcadores_perspectiva=_normalizar_marcadores(marcadores_brutos),
        perspectiva_nao_marcada=not marcadores_ok,
        metricas_fluencia=metricas,
    )
