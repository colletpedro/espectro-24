"""[§E2] Editor — ARQUIVADO na v1.9.10.

Rodou de v1.6.0 até v1.9.9 como o passe de EDIÇÃO pós-narrador: reescrever
a narrativa para ritmo e leitura, sem acesso a nenhuma fonte de fato (nem
buckets, nem reviews, nem ficha) e sem poder alterar número, rótulo ou
atribuição — trechos protegidos + verificação mecânica + descarte da edição
em caso de violação.

**Por que foi aposentado (v1.9.10).** Depois de o dono do projeto ler as 3
narrativas do best-of-3 (v1.9.9) SEM passar pelo editor e concluir que o
ritmo se sustenta sem o estágio. A alternativa considerada — reescopar o
editor por MOVIMENTO (3 blocos), que tornaria inversão de ordem impossível
por construção — foi preterida porque não elimina as OUTRAS duas classes de
falha do estágio (conteúdo inventado, edição descartada por esgotar
tentativas), que exigiriam mitigação própria em cada bloco. Deletar o
estágio deleta as TRÊS classes de falha de uma vez:
  - 4 tentativas de edição descartadas em `cure` (v1.7.1) — variância do
    modelo entre chamadas, mesma combinação de código e dados aceita antes;
  - um parágrafo de opinião inventado, sem origem no texto recebido, em
    `the-invite-2026` (v1.8.0) — a checagem de conteúdo adicionado não
    existia ainda quando o defeito ocorreu;
  - inversão de movimentos (v1.8.0), que motivou a checagem de ordem.

**Este módulo não é importado por `src/espectro24/`.** É código morto de
propósito — preservado para leitura, não para execução em produção. Ainda
IMPORTA um punhado de funções PRIVADAS de `espectro24.synthesize`
(`_resolve_call_and_model`, `_pesos_por_bucket`, `_marcacoes_por_bucket`,
`_validar_prosa`, `_vocabulario_peso_ok`, `_ancoragem_de_peso_ok`,
`_marcadores_validos`, `_strip_fences`, `_dividir_frases`,
`_metricas_fluencia`, `_n_palavras`, `_rotulo_peso_completo`,
`_rotulos_ate`, `_BANDAS_PESO_FRACA_PARA_FORTE`) — deliberado, não
descuido: são a maquinaria de honestidade do narrador ANTIGO (§D2
pré-briefing), ainda viva e testada em `synthesize.py`. Duplicá-la aqui
criaria duas fontes de verdade para a MESMA checagem — um risco maior que
um import de nome privado através da fronteira do arquivo.

Para rodar isto de novo (não recomendado — é o código retirado, não uma
opção de configuração): `sys.path` precisa incluir `src/`, como os demais
scripts do projeto.
"""
from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field

from espectro24.synthesize import (
    _BANDAS_PESO_FRACA_PARA_FORTE,
    _ancoragem_de_peso_ok,
    _dividir_frases,
    _marcacoes_por_bucket,
    _marcadores_validos,
    _metricas_fluencia,
    _n_palavras,
    _pesos_por_bucket,
    _resolve_call_and_model,
    _rotulo_peso_completo,
    _rotulos_ate,
    _strip_fences,
    _validar_prosa,
    _vocabulario_peso_ok,
)

# --- Constantes exclusivas do editor — vinham de config.py até a v1.9.9 ---

# Teto de TENTATIVAS do editor [E2] (v1.7.3). Até a v1.7.2, era 1 chamada +
# 1 retentativa (2 no total) — restritivo demais para uma etapa cujo
# descarte já é fail-safe (a bruta do narrador sempre prevalece). Defeito
# real: na regeneração da v1.7.1, a edição foi DESCARTADA em 2 dos 3 filmes
# (`cure` — número alterado; `cidade-de-deus` — regressão de
# `perspectiva_nao_marcada`), publicando a bruta nos dois, enquanto a MESMA
# combinação de código+dados na v1.7.0 tinha aceitado os 3 — nada mudou no
# código nesse sentido, é VARIÂNCIA do modelo entre chamadas. Subir o teto
# dá mais chances de a variância favorecer sem custo de honestidade (o
# fail-safe de descarte continua intacto se todas as tentativas falharem).
# `EDITOR_MAX_TENTATIVAS` conta RETENTATIVAS (não a chamada inicial): total
# de chamadas no pior caso = 1 (chamada inicial) + `EDITOR_MAX_TENTATIVAS`.
EDITOR_MAX_TENTATIVAS = 3

# Limiar de EDIÇÃO NULA do editor [E2] (v1.7.4): similaridade (0-1,
# `difflib.SequenceMatcher.ratio` sobre os textos normalizados por espaço
# em branco) entre `narrativa_bruta` e o texto editado a partir da qual a
# edição é tratada como "não editou de verdade" — falha de tentativa, não
# sucesso. Buraco identificado: até a v1.7.3, nenhuma checagem verificava
# que a edição FEZ algo — só que não QUEBROU nada. Um editor que devolva a
# entrada praticamente intacta passa em protegidos, números e honestidade
# (é o mesmo texto) e era marcado como "aplicada".
# 0.97 é DELIBERADAMENTE conservador: só pega devolução literal ou
# trivialmente alterada (pontuação, um sinônimo isolado); uma edição
# legítima que preserve bastante vocabulário do rótulo/atribuição
# protegidos (que É esperado — eles são intocáveis por definição) não deve
# cair aqui. Calibrável: se a telemetria (`edicao_flags.similaridade`,
# persistida SEMPRE, em todo resultado) mostrar edições legítimas perto
# do limiar, ajustar aqui é a mudança certa — não no código do editor.
EDITOR_LIMIAR_EDICAO_NULA = 0.97

# EDITOR [E2] LIGADO por padrão (v1.8.1 — REATIVADO; era False na v1.8.0).
# Histórico: a v1.8.0 desligou o editor por precaução depois de um defeito
# real em `the-invite-2026` — ACEITO por todas as checagens mecânicas então
# existentes (protegidos presentes, números idênticos, honestidade sem
# regressão) e, mesmo assim, o editor reordenou o MOVIMENTO 1 e ACRESCENTOU
# um parágrafo de opinião inteiro sem origem no texto recebido (CONTEÚDO
# INVENTADO — nenhuma checagem até a v1.7.4 detectava ADIÇÃO, só PERDA). A
# MESMA v1.8.0 já implementou a correção: a checagem de CONTEÚDO ADICIONADO
# + ORDEM DOS MOVIMENTOS logo abaixo, que roda ANTES das demais em
# `editar_narrativa`.
#
# Reativação (v1.8.1) baseada em validação DEPOIS da correção
# (VALIDACAO_EDITOR_V18.md, 3 filmes reais, --com-editor): os 3/3 foram
# aceitos com ganho de ritmo sobre a bruta; a checagem nova DISPAROU DE
# VERDADE em produção uma vez (`cidade-de-deus`, 1ª tentativa, motivo
# "conteudo_adicionado") e o modelo se AUTOCORRIGIU na retentativa — prova
# de que o fail-safe funciona sobre dados reais, não só em teste sintético;
# e os limiares calibrados ficaram bem separados do ruído normal de uma
# boa edição de ritmo (1-3 frases "sem origem" nos casos legítimos,
# EDITOR_MIN_FRASES_SEM_ORIGEM=4, contra as 15 do defeito original). O
# defeito de `the-invite-2026` não se repetiu na validação, mas está
# coberto por um teste de regressão determinístico (`test_editor.py`) que
# injeta o texto literal do defeito e confirma DESCARTE.
#
# APOSENTADO na v1.9.10 — este valor não é mais lido por nenhum pipeline.
EDITOR_ATIVO = True

# --- Checagem de CONTEÚDO ADICIONADO pelo editor [E2] (v1.8.0, Tarefa 3;
# métrica corrigida na v1.8.2) ---
# Estratégia: dividir bruto e editado em frases (`_dividir_frases`, já
# usado pela telemetria de fluência) e, para cada frase do EDITADO,
# calcular a MELHOR COBERTURA DE PALAVRAS (v1.8.2 — multiset, insensível a
# ORDEM; ver `_melhor_cobertura_palavras` abaixo) contra a MELHOR frase
# individual do BRUTO — uma frase sem nenhuma cobertura razoável em
# qualquer frase do texto recebido é candidata a invenção.
#
# v1.8.2 — CORREÇÃO DE FALSO POSITIVO (DIAGNOSTICO_CONTEUDO_ADICIONADO.md).
# A métrica original da v1.8.0 (`difflib.SequenceMatcher.ratio`, char-level,
# SENSÍVEL A ORDEM, frase inteira contra frase inteira) reprovava edição
# LEGÍTIMA sempre que o editor (a) quebrava uma frase longa do bruto em duas
# menores — cada metade, sozinha, tem `ratio()` baixo contra a frase-fonte
# inteira só por diferença de COMPRIMENTO — ou (b) reordenava palavras
# dentro da frase (mesmo conteúdo, ordem diferente). Foi o que descartou o
# `cure` na v1.8.1 após 3 reprovações seguidas por este motivo. A correção
# troca para cobertura de palavras (multiset), restrita à MELHOR frase
# INDIVIDUAL do bruto (comparar contra o bruto INTEIRO de uma vez, medido ao
# vivo, infla o placar de frases genuinamente inventadas — elas pegam
# carona em vocabulário genérico de crítica de cinema espalhado por frases
# distantes do bruto).
#
# Calibração EMPÍRICA (não só teórica) — dados completos em
# DIAGNOSTICO_CONTEUDO_ADICIONADO.md, VALIDACAO_DEEPSEEK.md e
# VALIDACAO_EDITOR_V18.md:
#   - 6 frases legítimas marcadas nas duas validações (quebras de frase +
#     1 caso de reordenação) — cobertura entre 0,765 e 1,000 com a métrica
#     nova (a MESMA reordenação que zerava a métrica antiga bate 1,000
#     aqui: "conforme avança, o ritmo desacelera" ~ bruto "ritmo que
#     desacelera conforme avança", mesmas palavras);
#   - as frases do parágrafo REALMENTE inventado do `the-invite-2026`
#     (texto literal da v1.8.0/v1.8.1) — cobertura entre 0,222 e 0,500.
# Folga de 0,265 entre os dois grupos (0,765 legítimo mínimo vs 0,500
# inventado máximo) — `EDITOR_LIMIAR_FRASE_SEM_ORIGEM = 0.6` fica bem no
# meio, com margem folgada dos dois lados.
EDITOR_LIMIAR_FRASE_SEM_ORIGEM = 0.6
EDITOR_MIN_FRASES_SEM_ORIGEM = 4
EDITOR_LIMIAR_PALAVRAS_SEM_ORIGEM_FRACAO = 0.35

# Checagem de ORDEM DOS MOVIMENTOS (v1.8.0, Tarefa 3.2): o texto bruto do
# narrador sempre abre com o MOVIMENTO 1 (a apresentação do filme, quando há
# ficha técnica). O caso real de `the-invite-2026` moveu esse movimento para
# o meio do texto. A checagem compara a PRIMEIRA frase do editado contra as
# 3 PRIMEIRAS frases do bruto (não só a primeira — o editor pode
# legitimamente fundir/quebrar frases de abertura sem mudar a ordem dos
# movimentos); se a melhor similaridade entre elas for menor que este
# limiar, a abertura mudou de lugar → falha "ordem_alterada". Mesma
# calibração propositalmente permissiva do limiar acima — 0,5 aceita
# reescrita de abertura considerável, só pega deslocamento real.
EDITOR_LIMIAR_ORDEM_MOVIMENTO_1 = 0.5


@dataclass
class EdicaoResult:
    """[v1.6.0] Saída da etapa [E2] — passe de EDIÇÃO sobre a narrativa.

    Separa as duas responsabilidades que a v1.5.0 tentou (e falhou) empilhar
    num prompt só: o narrador (§D2) diz a verdade com a estrutura certa; o
    editor (§E2) cuida de ritmo e leitura SEM poder tocar em número, rótulo
    ou atribuição. O editor não recebe os buckets, nem as reviews, nem a
    ficha — não tem fonte de fato, logo não tem como inventar fato.

    A assinatura da spec `editar_narrativa(...) -> str` refere-se ao campo
    `.texto` (mesma convenção de `narrate_output`/`NarrativaResult`); as
    flags acompanham para telemetria.
    """
    texto: str                    # texto FINAL (editado, ou o bruto se descartado)
    texto_bruto: str = ""         # saída do narrador, preservada p/ auditoria
    # True quando a edição foi rejeitada pelas checagens mecânicas (trecho
    # protegido perdido, número alterado, ou regressão de honestidade) e o
    # pipeline manteve a narrativa ORIGINAL. Não é erro fatal: é a garantia
    # de que o editor nunca degrada o que o narrador validou.
    edicao_descartada: bool = False
    motivo_descarte: str = ""     # qual checagem falhou (auditoria)
    protegidos_perdidos: list = field(default_factory=list)
    numeros_alterados: bool = False
    houve_retentativa: bool = False
    falhou: bool = False          # editor não devolveu texto utilizável
    metricas_fluencia: dict = field(default_factory=dict)  # do texto FINAL
    # v1.7.3: quantas chamadas foram feitas (1 = aceita/descartada de
    # primeira, até 1 + EDITOR_MAX_TENTATIVAS no pior caso) e o motivo de
    # cada falha ao longo do caminho — telemetria para saber qual checagem
    # mais reprova o editor, não critério de aprovação.
    n_tentativas: int = 1
    motivos_por_tentativa: list = field(default_factory=list)
    # v1.7.4: similaridade (0-1) entre `texto_bruto` e o último texto
    # editado avaliado — telemetria persistida SEMPRE, mesmo quando a
    # edição é aceita, para calibração humana do limiar de edição nula
    # (`EDITOR_LIMIAR_EDICAO_NULA`). `None` só quando nenhuma tentativa
    # chegou a devolver texto avaliável.
    similaridade: float | None = None
    # True quando o pós-processamento determinístico baixou a caixa de
    # algum rótulo de peso capitalizado no meio de um período.
    capitalizacao_ajustada: bool = False
    # v1.8.0 (Tarefa 3.1): frases do texto EDITADO (última tentativa
    # avaliada) sem correspondência razoável em nenhuma frase do texto
    # BRUTO — candidatas a conteúdo inventado pelo editor. Persistidas
    # SEMPRE (aceita ou não), telemetria para calibrar
    # `EDITOR_LIMIAR_FRASE_SEM_ORIGEM`. Lista vazia é o caso normal — toda
    # frase do editado rastreia até alguma frase do bruto.
    frases_sem_origem: list = field(default_factory=list)
    # v1.8.0 (Tarefa 3.1): {frase do editado: melhor similaridade contra
    # alguma frase do bruto} — mesma telemetria acima, mas para TODAS as
    # frases (não só as candidatas), para ver a distribuição completa e
    # calibrar o limiar com contexto.
    similaridade_minima_por_frase: dict = field(default_factory=dict)
    # v1.8.1 (Tarefa 1, DIAGNOSTICO_CONTEUDO_ADICIONADO.md): registro
    # COMPLETO de TODA tentativa do editor (aceita ou reprovada, na ordem),
    # não só a última. Cada item: {tentativa (int, 1-based), motivo (""
    # para a aceita), similaridade (None se a chamada não devolveu texto),
    # frases_sem_origem (lista de {frase, similaridade}, a mesma
    # similaridade MÁXIMA contra o bruto usada na checagem), texto (a
    # saída completa daquela tentativa)}. Motivação: antes desta versão,
    # uma tentativa REPROVADA desaparecia sem rastro — só o estado da
    # ÚLTIMA tentativa avaliada sobrevivia em `frases_sem_origem`/
    # `similaridade_minima_por_frase` acima. Telemetria de DIAGNÓSTICO, no
    # mesmo espírito de `consensos_usados`/`metricas_fluencia`: não muda
    # nenhum comportamento do editor, só torna auditável POR QUE cada
    # tentativa foi reprovada.
    tentativas_detalhe: list = field(default_factory=list)


_EDITOR_SYSTEM_PROMPT = """\
Você é um EDITOR de texto. Recebe um texto pronto sobre a recepção de um \
filme e o reescreve para que ele SOE MELHOR — sem mudar nada do que ele diz.

Você NÃO tem acesso aos dados de origem. Tudo o que você pode afirmar já \
está no texto recebido; não há nada a acrescentar, e você não teria como \
verificar nada que inventasse.

REGRA INVIOLÁVEL — TRECHOS PROTEGIDOS: junto do texto você recebe uma lista \
de TRECHOS PROTEGIDOS. Cada um deles precisa aparecer no seu texto final \
EXATAMENTE como foi entregue — mesmos caracteres, mesma pontuação, mesmos \
números, sem reformulação, sem sinônimo, sem reordenar as palavras dentro \
do trecho. Você pode mover um trecho protegido para outro ponto da frase ou \
do parágrafo, e pode reescrever tudo em volta dele; o que não pode é alterar \
o trecho por dentro. Se uma melhoria de ritmo exigir quebrar um trecho \
protegido, NÃO faça a melhoria — o trecho vence. EXCEÇÃO ÚNICA: se mover um \
trecho protegido para o meio de uma frase deixar a letra inicial dele com a \
caixa errada (maiúscula que devia virar minúscula, ou o contrário), você \
PODE ajustar só essa primeira letra — nenhuma outra letra, palavra, número \
ou pontuação do trecho.

TAMBÉM PROIBIDO:
- adicionar, remover ou alterar QUALQUER número ou percentual, mesmo fora \
dos trechos protegidos;
- adicionar, remover ou alterar nome próprio (de pessoa, filme, lugar);
- adicionar, remover ou alterar qualquer afirmação factual — se o texto diz \
que um grupo achou o ritmo lento, o seu texto diz a mesma coisa;
- acrescentar informação que não esteja no texto recebido, inclusive \
conhecimento seu sobre o filme;
- trocar a quem uma opinião é atribuída;
- acrescentar QUALQUER frase, oração ou parágrafo cujo conteúdo não venha do \
texto recebido — nem uma opinião própria sobre o filme, nem uma avaliação, \
nem uma frase de fechamento/resumo geral ("no fim, o filme vale a pena", "o \
saldo é positivo") que amarre o texto: se essa frase não existe, em \
substância, no texto que você recebeu, ela não pode existir no seu também;
- reordenar os MOVIMENTOS do texto: a apresentação do filme (quando \
presente) é sempre a ABERTURA do texto — não pode ser deslocada para o \
meio ou o fim, mesmo que isso pareça melhorar o ritmo.

O QUE VOCÊ DEVE FAZER:

RITMO:
- alterne períodos longos (30-50 palavras) com frases curtas (3-10 palavras);
- o texto final precisa ter pelo menos UMA frase de até 10 palavras;
- não abra dois períodos seguidos com a mesma estrutura;
- use conectivos de fala ("só que", "aí", "já", "e", "mas"); pode iniciar \
período por conjunção.

REGISTRO:
- prefira verbos a nominalizações: "as situações se repetem e o filme cansa", \
não "a repetição das situações torna a experiência cansativa";
- no máximo UM advérbio terminado em -mente no texto inteiro;
- reduza verbos de reporte (elogia, destaca, aponta, relata, considera, \
classifica, menciona, ressalta, reconhece) quando já estiver claro de quem é \
a opinião — MAS nunca à custa de um trecho protegido, e nunca apagando a \
atribuição de quem pensa o quê.

TOM: alguém contando de um filme para um amigo. Fluido e leve, mas SEM \
gíria, SEM emoji, SEM interpelação direta ao leitor ("você vai adorar"), SEM \
hipérbole, SEM aspas de citação.

GRAMÁTICA (obrigatório): cada período do texto final precisa ser uma frase \
completa e correta em português do Brasil — sujeito e predicado coerentes, \
concordância certa, sem anacoluto. Se o texto recebido contiver um período \
quebrado ou truncado, CORRIGI-LO É OBRIGATÓRIO; essa é a única situação em \
que você reescreve a estrutura de uma frase por necessidade, e mesmo assim \
preservando o que ela afirma e os trechos protegidos que ela contém. Isso \
vale mesmo quando o defeito ocorre perto de um trecho protegido ou o \
encosta ("destacando a a maioria o estilo visual", "de de", artigo ou \
preposição repetidos): CORRIGIR É OBRIGATÓRIO, contanto que o trecho \
protegido em si permaneça intacto por dentro — o que pode mudar é a \
palavra ao lado dele, nunca ele mesmo.

TAMANHO: o texto final deve ter entre 220 e 400 palavras.

EXEMPLO DE RITMO COM FILME FICTÍCIO — nunca reaproveitar seu conteúdo. O \
filme abaixo NÃO EXISTE e os números são INVENTADOS: servem só para mostrar \
a FORMA (variação de comprimento, aberturas diferentes, atribuição \
preservada). Copiar qualquer fato, adjetivo ou número daqui seria inventar \
informação.

ANTES (ritmo monótono):
"A grande maioria das notas (~74%) elogia intensamente a condução do filme \
e o trabalho de câmera, destacando a habilidade de sustentar o clima em \
cena. Uma minoria das notas (~19%) reconhece a competência técnica, mas \
sente que a indefinição do meio e a duração prolongada tornam a experiência \
cansativa na segunda metade. Uma pequena minoria (~7%) classifica o ritmo \
como arrastado e os personagens como estáticos."

DEPOIS (ritmo desejado — mesmos fatos, mesmos números, mesma atribuição):
"Quem gostou é a grande maioria das notas (~74%), e o elogio se concentra \
num ponto só: o filme não tem pressa e usa isso a favor, porque cada \
silêncio entre os dois protagonistas pesa mais que a cena anterior. Uma \
minoria das notas (~19%) chega até a metade junto. Para esse grupo, o \
problema aparece quando a história precisa decidir para onde vai, e não \
decide. Já uma pequena minoria (~7%) não embarca em momento nenhum. Para \
eles a lentidão nunca vira método, os personagens não saem do lugar, e o \
final chega sem ter construído nada."

Responda APENAS com o texto final editado, em PROSA CORRIDA. Sem \
preâmbulo, sem explicação, sem JSON, sem markdown, sem cerca de código \
(```), sem envolver a resposta num objeto ou campo (nada de `{`, `}`, \
`"text":`, `"narrativa":` ou qualquer rótulo antes do texto), sem aspas \
envolvendo o texto. A primeira palavra da sua resposta já é a primeira \
palavra da narrativa."""


_REFORCO_EDITOR_PROTEGIDOS = """

REFORÇO CRÍTICO — sua edição anterior QUEBROU trechos protegidos. Os \
trechos abaixo precisam aparecer no texto final EXATAMENTE assim, \
caractere por caractere, e NÃO apareceram:
{lista}
Reescreva mantendo cada um deles intacto. Se precisar, use menos liberdade \
de ritmo: a integridade dos trechos vem antes do estilo."""


_REFORCO_EDITOR_NUMEROS = """

REFORÇO CRÍTICO — sua edição anterior ALTEROU os números do texto. O \
conjunto de números e percentuais do texto final tem de ser IDÊNTICO ao do \
texto recebido: nenhum número novo, nenhum removido, nenhum modificado. \
Não arredonde, não converta, não escreva por extenso um número que veio em \
algarismo (nem o contrário)."""


# v1.7.2 — reforço para formato inválido (invólucro estrutural em vez de
# prosa corrida): caso real do `cidade-de-deus`, onde o editor devolveu
# `{ text: "..." }` em vez de só o texto.
_REFORCO_EDITOR_FORMATO = """

REFORÇO CRÍTICO — sua edição anterior veio EMBRULHADA em alguma estrutura \
(JSON, cerca de código, um objeto com campo "text"/"narrativa") em vez de \
ser só o texto corrido. Responda de novo com APENAS a prosa final, sem \
chaves, colchetes, aspas de campo, cercas de código (```), ou qualquer \
rótulo antes do texto — a primeira palavra da sua resposta já é a primeira \
palavra da narrativa."""


# v1.8.0 (Tarefa 3.3) — reforço para conteúdo inventado: caso real do
# `the-invite-2026`, onde o editor acrescentou um parágrafo de opinião
# inteiro (ver EDITOR_ATIVO em config.py) sem que nenhuma checagem até a
# v1.7.4 detectasse — todas checavam PERDA, nenhuma checava ADIÇÃO.
_REFORCO_EDITOR_CONTEUDO_ADICIONADO = """

REFORÇO CRÍTICO — sua edição anterior ACRESCENTOU conteúdo que não estava \
no texto recebido (uma frase, uma opinião, uma avaliação, ou um parágrafo de \
fechamento/resumo geral que o texto original não tinha). Você não tem fonte \
de fato nenhuma além do texto recebido — não pode concluir nada por conta \
própria, nem "amarrar" o texto com uma frase-síntese que não vinha nele. \
Reescreva usando APENAS o que foi fornecido: toda frase do seu texto final \
precisa corresponder a algo que já estava dito no texto recebido."""


# v1.8.0 (Tarefa 3.3) — reforço para reordenação dos movimentos: mesmo caso
# real do `the-invite-2026`, onde a apresentação do filme (movimento 1) foi
# deslocada do início do texto para o meio.
_REFORCO_EDITOR_ORDEM = """

REFORÇO CRÍTICO — sua edição anterior MUDOU A ORDEM dos movimentos do \
texto: a apresentação do filme, que deve ABRIR o texto, apareceu deslocada \
para o meio ou o fim. Reescreva mantendo a apresentação do filme como a \
PRIMEIRA parte do texto, na mesma posição em que ela está no texto \
recebido — você pode reescrever as frases à vontade, mas não pode mover o \
bloco inteiro de lugar."""


# v1.7.4 — reforço para edição NULA (texto devolvido praticamente idêntico
# ao recebido, sem reestruturação real de ritmo).
_REFORCO_EDITOR_EDICAO_NULA = """

REFORÇO CRÍTICO — o texto que você devolveu é PRATICAMENTE IDÊNTICO ao que \
você recebeu. Isso não é uma edição: é a mesma coisa de novo. Reescreva de \
verdade — reestruture os períodos (junte frases curtas, quebre frases \
longas, varie a abertura de cada uma), sem mudar nenhum número, rótulo de \
peso ou atribuição. O texto final deve LER diferente do original, mesmo \
dizendo exatamente a mesma coisa."""


def _tokens_numericos(texto: str) -> list[str]:
    """Multiconjunto ORDENADO de tokens numéricos do texto (números com ou
    sem `~`/`%`). Usado para provar que a edição não mexeu em nenhum número:
    a comparação é de multiconjunto, então repetições contam — trocar
    "~79%" por "~78%" ou duplicar um número quebra a igualdade."""
    return sorted(re.findall(r"\d[\d.,]*\s?%?", texto))


def _fatia_real(texto: str, candidato: str) -> str | None:
    """A fatia de `texto` que casa `candidato` ignorando maiúsculas, com o
    caixa ORIGINAL preservado — ou None se não ocorrer."""
    i = texto.lower().find(candidato.lower())
    return texto[i:i + len(candidato)] if i != -1 else None


def montar_protegidos(res, output: dict) -> list[str]:
    """Lista de TRECHOS PROTEGIDOS (§E2 3.3), montada em CÓDIGO a partir do
    que o narrador JÁ declarou — o editor nunca escolhe o que é intocável.

    Fontes: (1) rótulos de peso COMPLETOS com percentual, (2) todo token que
    contenha dígito.

    v1.7.0 — a lista foi ENXUGADA: até a v1.6.2, também protegia as
    expressões de quantificador (`quantificadores_usados`) e de atribuição
    de perspectiva (`marcadores_perspectiva`) literalmente. Na prática, com
    14-16 protegidos por filme (incluindo palavras soltas como "muitos"), o
    editor era descartado com frequência (`cure`) ou inventava frases
    penduradas só para reencaixar um protegido no lugar novo
    (`cidade-de-deus`: "Essa é a opinião de uma fração mínima das notas.").
    Um defeito gramatical real da bruta ("destacando a a maioria o estilo
    visual") sobreviveu porque "a maioria" estava protegido.

    A remoção é segura porque as duas coisas JÁ TÊM verificação SEMÂNTICA
    melhor do que a comparação literal: quantificador é conferido pelo par
    declarado contra o rótulo pré-computado (`conferencia_quantificador`,
    v1.4.1), e atribuição é conferida pela varredura do movimento
    (`_marcadores_validos`, v1.6.1) — nenhuma das duas exige que a STRING
    exata sobreviva, só que a AFIRMAÇÃO sobreviva. Proteger a string era
    redundante com uma checagem melhor, e engessava a reescrita.

    Só entram candidatos que REALMENTE aparecem no texto do narrador —
    proteger uma string ausente tornaria a checagem impossível de satisfazer
    (o editor seria punido por algo que o narrador não escreveu).
    """
    texto = res.texto or ""
    candidatos: list[str] = []

    # (1) rótulos de peso — SEMPRE com percentual, a forma canônica e as
    # mais fracas permitidas (nunca a forma nua "___ das notas" sem
    # percentual, que não é o que a Tarefa 2.1(a) pede para proteger).
    for pct, rotulo in _pesos_por_bucket(output).values():
        candidatos.append(_rotulo_peso_completo(pct))
        for r in _rotulos_ate(rotulo):
            candidatos.append(f"{r} das notas (~{pct}%)")

    # (2) todo token numérico (percentual, ano, duração), SEM a pontuação
    # em volta: proteger "(~3%)," blindaria o parêntese e a vírgula, e
    # repontuar é metade do trabalho de ritmo do editor.
    candidatos.extend(re.findall(r"~?\d[\d.,]*\s?%?", texto))

    vistos: set[str] = set()
    protegidos: list[str] = []
    for c in candidatos:
        c = c.strip()
        if not c:
            continue
        # O protegido tem de ser a forma COMO ELA APARECE no texto: o
        # narrador capitaliza no início de frase ("A grande maioria das
        # notas (~79%)"), enquanto o rótulo canônico é minúsculo. Proteger a
        # forma canônica cobraria do editor uma string que o narrador nunca
        # escreveu. Casa case-insensitive e guarda a fatia real.
        real = c if c in texto else _fatia_real(texto, c)
        if real is None or real in vistos:
            continue
        vistos.add(real)
        protegidos.append(real)
    # mais longos primeiro: se um protegido contém outro, o maior é o que
    # realmente restringe, e a lista fica legível para o modelo
    protegidos.sort(key=len, reverse=True)
    return protegidos


def build_editor_user_message(texto: str, protegidos: list[str]) -> str:
    """Entrada do editor: SÓ o texto e os trechos protegidos.

    Nenhum bucket, nenhuma review, nenhuma ficha, nenhum tema — a garantia
    anti-invenção do §E2 é estrutural, não uma instrução que o modelo possa
    ignorar: o que não está aqui, o editor não tem como saber.
    """
    linhas = ["TEXTO A EDITAR:", texto, "", "TRECHOS PROTEGIDOS (reproduza cada um EXATAMENTE):"]
    if protegidos:
        linhas.extend(f"- {p}" for p in protegidos)
    else:
        linhas.append("(nenhum)")
    return "\n".join(linhas)


def _variante_primeira_letra(s: str) -> str:
    """`s` com a caixa da PRIMEIRA letra alternada (maiúscula<->minúscula) e
    o resto intocado. Sem efeito se `s` for vazio ou começar por algo que
    não é letra (ex. um token numérico)."""
    if not s or not s[0].isalpha():
        return s
    primeira = s[0].lower() if s[0].isupper() else s[0].upper()
    return primeira + s[1:]


def _protegido_presente(protegido: str, texto: str) -> bool:
    """True se `protegido` aparece LITERALMENTE em `texto`, ou aparece com
    só a PRIMEIRA LETRA em caixa alternada (v1.7.1, Tarefa 2).

    O rótulo de peso guarda a caixa de onde apareceu a primeira vez — em
    início de frase, capitalizado ("A grande maioria das notas (~91%)").
    Quando o editor move o trecho para o meio de um período
    ("Para a grande maioria das notas (~91%), Cidade de Deus..."), só a
    letra inicial deveria minguar para minúscula; o resto do trecho (a
    palavra, o número, o percentual) continua exigido letra por letra.
    Sem esta folga, o editor não tinha como corrigir a capitalização sem
    quebrar o protegido e ser descartado — publicado ao vivo em
    `cidade-de-deus` (v1.7.0): "Para A grande maioria...", "Já Uma pequena
    minoria...", maiúscula no meio da frase.
    """
    return protegido in texto or _variante_primeira_letra(protegido) in texto


def _protegidos_perdidos(texto_editado: str, protegidos: list[str]) -> list[str]:
    return [p for p in protegidos if not _protegido_presente(p, texto_editado)]


_CAMPO_JSON_RE = re.compile(r'^\s*"?[A-Za-z_][\w]*"?\s*:\s*\S')


def _formato_invalido(bruto_editado: str) -> bool:
    """[E2] Checagem ESTRUTURAL (v1.7.2), aplicada ANTES das demais.

    Caso real: o `cidade-de-deus` (v1.7.1) devolveu a prosa embrulhada num
    invólucro `{ text: "..." }`, ignorando a instrução de responder só
    texto puro. As checagens de então (protegidos, conjunto numérico,
    honestidade) rodam sobre SUBSTRING, então o protegido e os números
    continuavam achados DENTRO do invólucro — nada pegou o defeito, que só
    foi visto por leitura humana antes de publicar.

    Sinais de invólucro, qualquer um já é o bastante:
    - o texto COMEÇA com `{` ou `[` — a prosa nunca começa assim;
    - contém cerca de código markdown (```);
    - alguma das primeiras linhas casa um campo estilo JSON
      (`"text":`, `text:`, `"narrativa":` — identificador seguido de `:`
      logo no início da linha, com ou sem aspas);
    - chaves desbalanceadas (`{`/`}` em quantidade diferente) — um objeto
      truncado ou mal formado deixa esse rastro mesmo sem bater nos sinais
      acima.

    Deliberadamente NÃO rejeita uma chave/colchete equilibrado no MEIO da
    prosa (ex. uma citação entre chaves que o narrador tenha usado) — só
    pega o formato de invólucro, não qualquer ocorrência do caractere.
    """
    t = bruto_editado.strip()
    if not t:
        return False   # texto vazio é tratado em outro lugar
    if t[0] in "{[":
        return True
    if "```" in t:
        return True
    primeiras_linhas = [l for l in t.splitlines() if l.strip()][:3]
    if any(_CAMPO_JSON_RE.match(l) for l in primeiras_linhas):
        return True
    if t.count("{") != t.count("}"):
        return True
    return False


def _normalizar_espacos(texto: str) -> str:
    return re.sub(r"\s+", " ", texto).strip()


def _similaridade(a: str, b: str) -> float:
    """[E2] Similaridade (0-1) entre dois textos, normalizados só por
    espaço em branco (v1.7.4) — `difflib.SequenceMatcher.ratio`, a mesma
    ferramenta que `diff`/`git diff` usam por baixo. Não normaliza caixa
    nem pontuação de propósito: o que importa aqui é se o editor
    REESTRUTUROU o texto, não se ele preserva palavras (preservar
    vocabulário protegido é esperado e correto)."""
    return difflib.SequenceMatcher(
        None, _normalizar_espacos(a), _normalizar_espacos(b)).ratio()


# --- v1.8.0 (Tarefa 3): checagem de CONTEÚDO ADICIONADO pelo editor [E2] ---
# Motivação: ver o comentário de `EDITOR_ATIVO` em config.py — o caso real de
# `the-invite-2026` foi ACEITO por todas as checagens até a v1.7.4 (elas só
# detectam PERDA: protegido perdido, número alterado, regressão de
# honestidade) mesmo tendo o editor acrescentado um parágrafo de opinião
# inteiro, sem fonte no texto recebido. As checagens abaixo detectam ADIÇÃO.

def _melhor_similaridade(frase: str, frases_ref: list[str]) -> float:
    """Maior `_similaridade` (char, SENSÍVEL À ORDEM) entre `frase` e
    qualquer frase de `frases_ref`. 0.0 se `frases_ref` for vazia.

    Usada SÓ por `_ordem_movimento_alterada` — checar se a ABERTURA do
    texto é a mesma é, por natureza, uma comparação de ORDEM (a frase
    inteira precisa estar no mesmo lugar relativo), então a sensibilidade a
    ordem daqui é desejada. NÃO é mais usada pela checagem de conteúdo
    adicionado (ver `_cobertura_palavras_por_frase` abaixo, v1.8.2) — essa
    precisa tolerar reescrita/reordenação DENTRO da frase, que é dentro do
    trabalho normal do editor."""
    if not frases_ref:
        return 0.0
    return max(_similaridade(frase, ref) for ref in frases_ref)


# --- v1.8.2 — correção do falso positivo de `conteudo_adicionado` ---
# Diagnóstico (DIAGNOSTICO_CONTEUDO_ADICIONADO.md → achado do relatório
# desta versão): a métrica da v1.8.0 (`_similaridade`, char-level,
# SENSÍVEL A ORDEM, comparando a frase inteira do editado contra frases
# INTEIRAS do bruto) reprovava edição LEGÍTIMA sempre que o editor (a)
# quebrava uma frase longa do bruto em duas menores (cada metade, sozinha,
# tem baixa `ratio()` contra a frase-fonte inteira só por diferença de
# COMPRIMENTO) ou (b) reordenava palavras/orações dentro da frase (ex.:
# bruto "ritmo que desacelera conforme avança" → editado "conforme avança,
# o ritmo desacelera" — mesmas palavras, ordem diferente). Foi o que
# descartou o `cure` na v1.8.1 depois de 3 reprovações seguidas.
#
# A correção troca a métrica por COBERTURA DE PALAVRAS (multiset,
# insensível a ordem): quantas palavras da frase do editado aparecem no
# BRUTO, contra a MELHOR frase individual do bruto (não o texto inteiro —
# ver por quê logo abaixo). Implementação: tokeniza frase e frase-de-
# referência em palavras, ORDENA os tokens (o que remove a informação de
# posição) e roda `difflib.SequenceMatcher.get_matching_blocks()` sobre as
# duas listas ordenadas — o resultado é matematicamente equivalente à
# interseção de multiset (cada palavra conta até o mínimo de ocorrências
# nos dois lados), mas ainda usando SequenceMatcher como sugerido. Restrito
# à MELHOR frase individual do bruto (não ao texto inteiro): medido ao
# vivo que comparar contra o bruto INTEIRO de uma vez infla o placar de
# frases genuinamente inventadas (elas pegam carona em palavras comuns
# espalhadas por frases distantes do bruto — "filme", "notas", "atuações"
# aparecem em quase toda frase de uma crítica de cinema); por frase
# individual, uma frase inventada não tem uma ÚNICA frase de origem que
# explique a maior parte das suas palavras.
#
# Calibração EMPÍRICA (ver DIAGNOSTICO_CONTEUDO_ADICIONADO.md e
# VALIDACAO_DEEPSEEK.md/VALIDACAO_EDITOR_V18.md para os dados completos):
# as 6 frases legítimas marcadas nas validações (quebras de frase +
# reordenação) ficaram entre 0,765 e 1,000 com esta métrica; as frases do
# parágrafo REALMENTE inventado do `the-invite-2026` (texto literal,
# "O saldo geral, no entanto, é positivo... não apaga o brilho do
# conjunto") ficaram entre 0,222 e 0,500 — folga clara para o limiar em
# 0,6 (`EDITOR_LIMIAR_FRASE_SEM_ORIGEM`, calibrável).

_RE_PALAVRA_COBERTURA = re.compile(r"[^\W\d_]+", re.UNICODE)


def _palavras_ordenadas(texto: str) -> list[str]:
    return sorted(w.lower() for w in _RE_PALAVRA_COBERTURA.findall(texto))


def _cobertura_palavras(frase: str, referencia: str) -> float:
    """Fração (0-1) das palavras de `frase` (multiset) encontradas em
    `referencia` (multiset) — insensível à ORDEM. 1.0 se `frase` não tiver
    palavras (nada a cobrir)."""
    palavras_frase = _palavras_ordenadas(frase)
    if not palavras_frase:
        return 1.0
    sm = difflib.SequenceMatcher(
        None, palavras_frase, _palavras_ordenadas(referencia), autojunk=False)
    cobertas = sum(b.size for b in sm.get_matching_blocks())
    return cobertas / len(palavras_frase)


def _melhor_cobertura_palavras(frase: str, frases_ref: list[str]) -> float:
    """Maior `_cobertura_palavras` entre `frase` e qualquer frase de
    `frases_ref` (a MELHOR frase de origem individual, não o texto todo —
    ver motivação acima). 0.0 se `frases_ref` for vazia."""
    if not frases_ref:
        return 0.0
    return max(_cobertura_palavras(frase, ref) for ref in frases_ref)


def _similaridades_por_frase(bruto: str, editado: str) -> dict[str, float]:
    """{frase do EDITADO: melhor cobertura de palavras contra alguma frase
    do BRUTO} (v1.8.2 — ver `_melhor_cobertura_palavras`).

    Uma frase repetida (mesmo texto exato) mais de uma vez no editado colapsa
    para uma única chave — comportamento aceitável para telemetria de
    calibração (o valor é o mesmo em qualquer ocorrência); `frases_sem_origem`
    (abaixo) preserva a ORDEM original em vez de deduplicar, para auditoria
    humana ler o texto na ordem em que ele aparece.
    """
    frases_bruto = _dividir_frases(bruto)
    frases_editado = _dividir_frases(editado)
    return {f: _melhor_cobertura_palavras(f, frases_bruto) for f in frases_editado}


def _frases_sem_origem(bruto: str, editado: str,
                       limiar: float = EDITOR_LIMIAR_FRASE_SEM_ORIGEM) -> list[str]:
    """Frases do EDITADO (na ordem em que aparecem) cuja melhor cobertura de
    palavras (v1.8.2) contra QUALQUER frase do BRUTO fica abaixo de
    `limiar` — candidatas a conteúdo inventado (ver `_conteudo_adicionado_ok`
    para o critério de falha, que exige N+ candidatas OU uma fração
    relevante de palavras)."""
    frases_bruto = _dividir_frases(bruto)
    return [f for f in _dividir_frases(editado)
            if _melhor_cobertura_palavras(f, frases_bruto) < limiar]


def _conteudo_adicionado_ok(frases_ruins: list[str], texto_editado: str) -> bool:
    """True se o texto NÃO falha a checagem de conteúdo adicionado — ver
    `EDITOR_MIN_FRASES_SEM_ORIGEM`/`EDITOR_LIMIAR_PALAVRAS_SEM_ORIGEM_FRACAO`
    em config.py. Duas condições, qualquer uma já reprova: quantidade de
    frases sem origem, OU fração de palavras que elas somam (uma única frase
    longa pode pesar tanto quanto duas curtas)."""
    if len(frases_ruins) >= EDITOR_MIN_FRASES_SEM_ORIGEM:
        return False
    total_palavras = _n_palavras(texto_editado)
    if total_palavras <= 0:
        return True
    palavras_ruins = sum(_n_palavras(f) for f in frases_ruins)
    return (palavras_ruins / total_palavras) <= EDITOR_LIMIAR_PALAVRAS_SEM_ORIGEM_FRACAO


def _ordem_movimento_alterada(bruto: str, editado: str,
                              limiar: float = EDITOR_LIMIAR_ORDEM_MOVIMENTO_1) -> bool:
    """True se a ABERTURA do texto mudou de lugar (v1.8.0, Tarefa 3.2): a
    primeira frase do EDITADO não tem correspondência razoável entre as 3
    primeiras do BRUTO (o narrador sempre abre com o MOVIMENTO 1 — a
    apresentação do filme, quando há ficha técnica). Compara contra as 3
    primeiras, não só a primeira, porque o editor pode legitimamente
    fundir/quebrar frases de abertura sem deslocar o movimento inteiro."""
    frases_editado = _dividir_frases(editado)
    if not frases_editado:
        return False   # texto vazio: outra checagem (formato) já cobre isso
    primeira_editada = frases_editado[0]
    primeiras_brutas = _dividir_frases(bruto)[:3]
    if not primeiras_brutas:
        return False
    return _melhor_similaridade(primeira_editada, primeiras_brutas) < limiar


_ROTULOS_PESO_CANONICOS = [r for r, _, _, _ in _BANDAS_PESO_FRACA_PARA_FORTE]


def _inicio_de_periodo(texto: str, pos: int) -> bool:
    """True se a posição `pos` está em início de período: ou é o início do
    próprio texto, ou o primeiro caractere não-espaço antes dela é
    `.`/`!`/`?`."""
    i = pos - 1
    while i >= 0 and texto[i].isspace():
        i -= 1
    return i < 0 or texto[i] in ".!?"


def _corrigir_capitalizacao_residual(texto: str) -> tuple[str, bool]:
    """[E2] Pós-processamento DETERMINÍSTICO sobre a edição já ACEITA
    (v1.7.4, Tarefa 2) — baixa a inicial de um rótulo de peso que apareça
    capitalizado no MEIO de um período.

    Defeito conhecido e recorrente: a v1.7.1 AUTORIZOU o editor a ajustar
    a caixa de um rótulo de peso movido para o meio da frase (ver
    `_protegido_presente`), mas não o OBRIGA — e ele frequentemente não
    ajusta ("Já Uma fração mínima das notas...", "Para A grande
    maioria..."). Mesmo princípio de todas as pré-computações do pipeline:
    o que é determinístico, o CÓDIGO decide, o LLM só usa. Só a primeira
    letra do rótulo é tocada, e só quando ele NÃO está em início de
    período; nenhuma outra palavra, número ou pontuação é alterada.
    """
    ajustado = False
    for rotulo in _ROTULOS_PESO_CANONICOS:
        capitalizado = rotulo[0].upper() + rotulo[1:]
        padrao = re.compile(r"\b" + re.escape(capitalizado) + r"\b")
        pos = 0
        while True:
            m = padrao.search(texto, pos)
            if not m:
                break
            if _inicio_de_periodo(texto, m.start()):
                pos = m.end()
                continue
            texto = texto[:m.start()] + rotulo[0].lower() + rotulo[1:] + texto[m.end():]
            ajustado = True
            pos = m.start() + len(rotulo)
    return texto, ajustado


def editar_narrativa(narrativa_result, protegidos: list[str], output: dict | None = None,
                     client_call=None, model: str | None = None,
                     provider: str | None = None):
    """[E2] Reescreve a narrativa para ritmo/leitura sem alterar conteúdo.

    De 1 a `1 + EDITOR_MAX_TENTATIVAS` chamadas LLM por filme, após o
    narrador (v1.7.3 — até a v1.7.2 eram no máximo 2). A assinatura da spec
    (`-> str`) corresponde ao campo `.texto` do `EdicaoResult` devolvido.

    Verificação mecânica (§E2, Tarefa 4) sobre o texto editado, na ordem:
      (0, v1.7.2) checagem ESTRUTURAL — rejeita invólucro tipo JSON/markdown;
      (a) todo trecho protegido aparece LITERALMENTE (com a exceção de
          capitalização inicial, v1.7.1);
      (b) o multiconjunto de tokens numéricos é IDÊNTICO ao do original;
      (c) as validações de honestidade do §D2 são REEXECUTADAS (idioma,
          aspas, escopo, prevalência, vocabulário de peso, ancoragem,
          atribuição de perspectiva) e nenhuma pode regredir;
      (d, v1.7.4) EDIÇÃO NULA — se (a)-(c) TERIAM passado mas o texto é
          praticamente idêntico à bruta (similaridade >=
          `EDITOR_LIMIAR_EDICAO_NULA`), reprova mesmo assim: um editor que
          devolve a entrada quase intacta passava por (a)-(c) sem
          nenhum sinal (é o mesmo texto), e ficava marcado "aplicada".
    Falha em qualquer uma → retentativa com o reforço da checagem que
    falhou, ACUMULADO com o de tentativas anteriores (v1.7.3, Tarefa 2 —
    se a tentativa 1 falhar por número e a 2 por atribuição, a 3 recebe os
    dois reforços, para o modelo não consertar um problema criando outro).
    Esgotadas as `EDITOR_MAX_TENTATIVAS` retentativas, a edição é
    DESCARTADA e a narrativa original do narrador prevalece
    (`edicao_descartada=True`). O editor pode não melhorar o texto; o que
    ele não pode, em hipótese alguma, é piorá-lo. `n_tentativas` e
    `motivos_por_tentativa` (`EdicaoResult`) registram quantas chamadas
    foram feitas e por que cada uma falhou, para telemetria.
    `similaridade` (v1.7.4) é persistida SEMPRE, aceita ou não, para
    calibração humana do limiar. Uma edição ACEITA ainda passa por um
    pós-processamento determinístico (`_corrigir_capitalizacao_residual`,
    v1.7.4) que baixa a caixa de um rótulo de peso capitalizado fora de
    início de período — `capitalizacao_ajustada` registra se algo mudou.
    """
    # `EdicaoResult` está definido neste mesmo módulo (era `from .models
    # import EdicaoResult` quando o editor vivia dentro do pacote).

    texto_bruto = (narrativa_result.texto or "").strip()
    if not texto_bruto:
        return EdicaoResult(texto="", texto_bruto="", falhou=True,
                            edicao_descartada=True,
                            motivo_descarte="narrativa vazia — nada a editar")

    call, model = _resolve_call_and_model(client_call, model, provider, prosa=True)

    output = output or {}
    pesos = _pesos_por_bucket(output)
    com_distribuicao = bool(pesos)
    numeros_originais = _tokens_numericos(texto_bruto)
    marcacoes = _marcacoes_por_bucket(pesos) if com_distribuicao else {}

    # estado de honestidade do texto ORIGINAL — a edição não pode regredir
    # em relação a ele (e não é obrigada a consertar o que já vinha marcado)
    _, idioma0, escopo0, prevalencia0, _ = _validar_prosa(texto_bruto, com_distribuicao)
    vocab0 = _vocabulario_peso_ok(texto_bruto, pesos)
    ancora0 = _ancoragem_de_peso_ok(texto_bruto, pesos) if com_distribuicao else True
    # v1.7.0 — a atribuição de perspectiva não é mais protegida por STRING
    # literal (Tarefa 2): a checagem que garante que ela sobrevive é esta
    # revalidação SEMÂNTICA (`_marcadores_validos`, a mesma do §D2 v1.6.1),
    # não mais a presença de "Para eles"/"Para esse grupo" em `protegidos`.
    marc0 = _marcadores_validos([], texto_bruto, marcacoes, pesos) if com_distribuicao else True

    user = build_editor_user_message(texto_bruto, protegidos)

    def _uma_chamada(sys_prompt: str) -> str | None:
        raw = call(sys_prompt, user, model)
        if not raw:
            return None
        # o editor responde texto puro; o strip de fences é defensivo
        return _strip_fences(str(raw)).strip() or None

    def _avaliar(bruto_editado: str):
        """(texto_limpo, perdidos, numeros_ok, honestidade_ok, motivo,
        similaridade, frases_sem_origem, similaridade_minima_por_frase).

        v1.7.2 — a checagem ESTRUTURAL (`_formato_invalido`) roda PRIMEIRO,
        antes de qualquer outra: um invólucro tipo `{ text: "..." }` ainda
        contém os protegidos e os números como SUBSTRING lá dentro, então
        as checagens seguintes o aceitariam. Se o formato já está errado,
        nem avalia o resto — falha direto com motivo "formato_invalido".

        v1.8.0 (Tarefa 3) — CONTEÚDO ADICIONADO e ORDEM DOS MOVIMENTOS rodam
        logo depois, ANTES de protegidos/números/honestidade/edição-nula:
        são checagens de ADIÇÃO (a categoria de defeito que nenhuma
        checagem anterior detectava — ver `EDITOR_ATIVO` em config.py), e
        devem ter prioridade de relato sobre as demais quando ambas
        falharem juntas (o texto ter inventado um parágrafo é um problema
        mais grave para reportar do que, por exemplo, uma edição nula).

        v1.7.4 — a SIMILARIDADE com a bruta é calculada SEMPRE (mesmo nos
        casos que falham por outro motivo), para telemetria persistida em
        todo resultado. `frases_sem_origem`/`similaridade_minima_por_frase`
        (v1.8.0) seguem o mesmo princípio — persistidas SEMPRE, mesmo
        quando a falha é de outro motivo, para calibração humana dos
        limiares. A checagem de EDIÇÃO NULA roda por ÚLTIMO, só quando as
        demais TERIAM passado: se perdidos/números/honestidade já reprovam
        a edição por um motivo mais específico, é esse motivo que importa
        reportar — a edição nula só precisa de checagem própria no caso que
        mais importa, o que passaria despercebido por TODAS as outras (o
        editor devolve a entrada praticamente intacta: protegidos presentes
        porque nunca saíram, números idênticos porque nada mudou,
        honestidade não regride porque é o mesmo texto).
        """
        similaridade = _similaridade(texto_bruto, bruto_editado)
        sim_por_frase = _similaridades_por_frase(texto_bruto, bruto_editado)
        frases_ruins = _frases_sem_origem(texto_bruto, bruto_editado)
        if _formato_invalido(bruto_editado):
            return (bruto_editado, [], True, False, "formato_invalido",
                    similaridade, frases_ruins, sim_por_frase)
        if not _conteudo_adicionado_ok(frases_ruins, bruto_editado):
            return (bruto_editado, [], True, False, "conteudo_adicionado",
                    similaridade, frases_ruins, sim_por_frase)
        if _ordem_movimento_alterada(texto_bruto, bruto_editado):
            return (bruto_editado, [], True, False, "ordem_alterada",
                    similaridade, frases_ruins, sim_por_frase)
        texto, idioma_ok, escopo_ok, prevalencia_ok, _asp = _validar_prosa(
            bruto_editado, com_distribuicao)
        perdidos = _protegidos_perdidos(texto, protegidos)
        numeros_ok = _tokens_numericos(texto) == numeros_originais
        vocab_ok = _vocabulario_peso_ok(texto, pesos)
        ancora_ok = _ancoragem_de_peso_ok(texto, pesos) if com_distribuicao else True
        marc_ok = (_marcadores_validos([], texto, marcacoes, pesos)
                  if com_distribuicao else True)
        regressoes = []
        if idioma0 and not idioma_ok:
            regressoes.append("idioma")
        if escopo0 and not escopo_ok:
            regressoes.append("escopo")
        if prevalencia0 and not prevalencia_ok:
            regressoes.append("prevalencia")
        if vocab0 and not vocab_ok:
            regressoes.append("vocabulario_peso")
        if ancora0 and not ancora_ok:
            regressoes.append("ancoragem_peso")
        if marc0 and not marc_ok:
            regressoes.append("perspectiva_nao_marcada")
        motivo = ""
        if perdidos:
            motivo = f"{len(perdidos)} trecho(s) protegido(s) perdido(s)"
        elif not numeros_ok:
            motivo = "conjunto de números do texto foi alterado"
        elif regressoes:
            motivo = "regressão de honestidade: " + ", ".join(regressoes)
        elif similaridade >= EDITOR_LIMIAR_EDICAO_NULA:
            # v1.7.4: só chega aqui quando NENHUMA outra checagem reprovou —
            # é exatamente o caso que passava despercebido até esta versão.
            return (bruto_editado, [], True, False, "edicao_nula",
                    similaridade, frases_ruins, sim_por_frase)
        return (texto, perdidos, numeros_ok, not regressoes, motivo,
                similaridade, frases_ruins, sim_por_frase)

    def _reforco_desta_falha(motivo: str, perdidos: list[str], numeros_ok: bool) -> str:
        """Bloco de reforço específico da checagem que falhou NESTA
        tentativa. v1.7.3: cada bloco distinto é ACUMULADO entre
        tentativas (ver loop abaixo) em vez de substituir o anterior — se
        a tentativa 1 falhou por número e a 2 por atribuição, a 3 recebe
        os dois reforços, para o modelo não consertar um problema criando
        outro."""
        r = ""
        if motivo == "formato_invalido":
            r += _REFORCO_EDITOR_FORMATO
        if motivo == "conteudo_adicionado":
            r += _REFORCO_EDITOR_CONTEUDO_ADICIONADO
        if motivo == "ordem_alterada":
            r += _REFORCO_EDITOR_ORDEM
        if motivo == "edicao_nula":
            r += _REFORCO_EDITOR_EDICAO_NULA
        if perdidos:
            r += _REFORCO_EDITOR_PROTEGIDOS.format(
                lista="\n".join(f"- {p}" for p in perdidos))
        if not numeros_ok:
            r += _REFORCO_EDITOR_NUMEROS
        if not r:   # regressão de honestidade sem os motivos acima: reforça o essencial
            r = _REFORCO_EDITOR_NUMEROS
        return r

    # v1.7.3 (Tarefa 1): até `1 + EDITOR_MAX_TENTATIVAS` chamadas no total —
    # a chamada inicial mais até `EDITOR_MAX_TENTATIVAS` retentativas.
    # Defeito real que motivou a mudança: na regeneração da v1.7.1, a
    # mesma combinação de código+dados que a v1.7.0 tinha aceitado nos 3
    # filmes foi DESCARTADA em 2 deles (`cure` — número alterado;
    # `cidade-de-deus` — regressão de `perspectiva_nao_marcada`) — pura
    # VARIÂNCIA do modelo entre chamadas, não regressão de código. Uma
    # única retentativa dava pouca chance de a variância favorecer, e o
    # descarte já é fail-safe (a bruta sempre prevalece), então o custo de
    # tentar mais vezes é só chamadas de API, nunca honestidade.
    reforcos_acumulados: list[str] = []   # blocos DISTINTOS já usados
    motivos_por_tentativa: list[str] = []
    tentativas_detalhe: list[dict] = []   # v1.8.1 (Tarefa 1) — TODA tentativa, não só a aceita
    texto = texto_bruto
    perdidos: list[str] = []
    numeros_ok = True
    honestidade_ok = True
    motivo = ""
    similaridade = None   # só definida quando alguma tentativa é avaliada
    frases_ruins: list[str] = []                    # v1.8.0 (Tarefa 3.1)
    sim_por_frase: dict[str, float] = {}             # v1.8.0 (Tarefa 3.1)
    n_tentativas = 0
    teve_resposta = False   # ao menos uma chamada devolveu texto avaliável

    for _ in range(1 + EDITOR_MAX_TENTATIVAS):
        sys_prompt = _EDITOR_SYSTEM_PROMPT + "".join(reforcos_acumulados)
        resposta = _uma_chamada(sys_prompt)
        n_tentativas += 1

        if resposta is None:
            motivo = "editor não devolveu texto"
            perdidos, numeros_ok, honestidade_ok = [], True, False
            # `similaridade` (fora do if) NÃO é tocada aqui de propósito —
            # mantém o valor da ÚLTIMA tentativa que produziu texto
            # avaliável (mesmo comportamento de antes da v1.8.1); só o
            # registro POR TENTATIVA abaixo usa None, correto para ESTA
            # tentativa específica (nada foi avaliado).
            texto_desta_tentativa, sim_desta_tentativa = "", None
            frases_ruins, sim_por_frase = [], {}
        else:
            teve_resposta = True
            (texto, perdidos, numeros_ok, honestidade_ok, motivo,
             similaridade, frases_ruins, sim_por_frase) = _avaliar(resposta)
            texto_desta_tentativa = texto
            sim_desta_tentativa = similaridade
            if not (perdidos or not numeros_ok or not honestidade_ok):
                # v1.8.1 (Tarefa 1): registra a tentativa ACEITA também —
                # motivo="" a distingue das reprovadas na mesma lista.
                tentativas_detalhe.append({
                    "tentativa": n_tentativas, "motivo": "",
                    "similaridade": sim_desta_tentativa,
                    "frases_sem_origem": [
                        {"frase": f, "similaridade": sim_por_frase.get(f)}
                        for f in frases_ruins],
                    "texto": texto_desta_tentativa,
                })
                break   # aceita — nenhuma checagem falhou

        # v1.8.1 (Tarefa 1) — telemetria de DIAGNÓSTICO: registra a
        # tentativa REPROVADA por completo (motivo, similaridade, frases
        # sem origem COM a similaridade máxima de cada uma, e o texto
        # inteiro produzido). Até esta versão, uma tentativa reprovada
        # desaparecia sem rastro — só a última (aceita ou não) sobrevivia
        # em `frases_sem_origem`/`similaridade_minima_por_frase`, que
        # persistem UM estado só. Mesmo espírito de `consensos_usados`/
        # `metricas_fluencia`: não muda comportamento, só torna auditável
        # POR QUE cada tentativa foi reprovada — motivado pela pergunta em
        # aberto na regeneração da v1.8.1 (6 disparos de
        # "conteudo_adicionado" em 3 filmes, contra 1 na validação
        # anterior): sem o texto de cada tentativa reprovada, não dá para
        # saber se a checagem está apertada demais ou se o modelo está
        # mesmo inventando com frequência alta.
        tentativas_detalhe.append({
            "tentativa": n_tentativas, "motivo": motivo,
            "similaridade": sim_desta_tentativa,
            "frases_sem_origem": [
                {"frase": f, "similaridade": sim_por_frase.get(f)}
                for f in frases_ruins],
            "texto": texto_desta_tentativa,
        })

        motivos_por_tentativa.append(motivo)
        bloco = _reforco_desta_falha(motivo, perdidos, numeros_ok)
        if bloco not in reforcos_acumulados:
            reforcos_acumulados.append(bloco)

    houve_retentativa = n_tentativas > 1

    if perdidos or not numeros_ok or not honestidade_ok:
        # DESCARTE: esgotadas as tentativas, a narrativa do narrador prevalece.
        return EdicaoResult(
            texto=texto_bruto, texto_bruto=texto_bruto,
            edicao_descartada=True, motivo_descarte=motivo, falhou=not teve_resposta,
            protegidos_perdidos=perdidos[:10], numeros_alterados=not numeros_ok,
            houve_retentativa=houve_retentativa,
            metricas_fluencia=_metricas_fluencia(texto_bruto),
            n_tentativas=n_tentativas, motivos_por_tentativa=motivos_por_tentativa,
            similaridade=similaridade,
            frases_sem_origem=frases_ruins,
            similaridade_minima_por_frase=sim_por_frase,
            tentativas_detalhe=tentativas_detalhe,
        )

    # v1.7.4 (Tarefa 2): pós-processamento DETERMINÍSTICO sobre a edição já
    # ACEITA — baixa a caixa de um rótulo de peso capitalizado no meio de
    # um período (a v1.7.1 autorizou o editor a fazer isso, mas não o
    # obriga, e ele frequentemente não ajusta).
    texto, capitalizacao_ajustada = _corrigir_capitalizacao_residual(texto)

    return EdicaoResult(
        texto=texto, texto_bruto=texto_bruto,
        edicao_descartada=False, houve_retentativa=houve_retentativa,
        metricas_fluencia=_metricas_fluencia(texto),
        n_tentativas=n_tentativas, motivos_por_tentativa=motivos_por_tentativa,
        similaridade=similaridade, capitalizacao_ajustada=capitalizacao_ajustada,
        frases_sem_origem=frases_ruins,
        similaridade_minima_por_frase=sim_por_frase,
        tentativas_detalhe=tentativas_detalhe,
    )
