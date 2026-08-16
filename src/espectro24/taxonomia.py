"""[v1.9.14, §2.5] A TAXONOMIA — a única definição dos 10 eixos.

Estava em `scripts/classificar_10.py`, que é script de medição. Subiu para
`src/` porque a v1.9.14 lhe deu um segundo consumidor de PRODUÇÃO: a
rotulagem de temas por eixo (§[D3], `rotulagem.py`), que precisa das MESMAS
definições, byte a byte. Duas cópias das dez definições seria a fonte de
divergência mais barata de criar e mais cara de achar — o rótulo mudaria de
sentido sem que `taxonomia_id` mudasse.

**A mudança é de lugar, não de conteúdo.** `SYSTEM` e `EIXOS` são os mesmos
bytes de antes; `taxonomia_id()` continua devolvendo `ebab2667de74`, e há
teste que trava esse valor desde a promoção de `A_regra`
(`tests/test_promocao_a_regra.py`). Se um byte tivesse mudado no caminho, o
id mudaria e a classificação inteira do catálogo deixaria de casar — que é
precisamente a proteção para a qual o id existe.

**A quem cabe o quê:** este módulo define; `scripts/classificar_10.py`
classifica review a review (auditado, votação de 3, precisão/recall medidos
por eixo); `rotulagem.py` rotula tema por eixo (§[D3], NÃO calibrado, e a
assimetria está declarada lá e na spec); `eixos.py` conta e calcula lift,
sem LLM nenhum.
"""
from __future__ import annotations

import hashlib

LIVRE = "livre"

EIXOS = (
    "ritmo",
    "atuacao",
    "direcao_imagem",
    "roteiro_estrutura",
    "som_trilha",
    "tom_atmosfera",
    "impacto_emocional",
    "comparacoes",
    "expectativa",
    "critica_social",
)
EIXOS_VALIDOS = set(EIXOS) | {"livre"}

SYSTEM = """Você classifica UMA review de cinema por vez segundo uma taxonomia fechada de EIXOS.

Os eixos disponíveis são exatamente estes:

- ritmo: velocidade, duração, arrasta/prende, edição no sentido de andamento, tédio ou tensão sustentada.
- atuacao: desempenho do elenco, performance de um ator ou atriz, elenco, direção de atores.
- direcao_imagem: fotografia, planos, cor, luz, composição, cenário, figurino, efeitos visuais, direção no sentido visual.
- roteiro_estrutura: história, enredo, estrutura, diálogos, personagens, final, coerência, previsibilidade.
- som_trilha: trilha sonora, música, som, mixagem, silêncio, canções.
- tom_atmosfera: clima, atmosfera, humor, registro, se é sério ou cômico, sensação de estranheza, ambiência.
- impacto_emocional: o efeito que o filme causou em quem escreveu, ou na plateia da sessão — chorou, riu, se arrepiou, sentiu nojo, saiu abalado, se identificou, teve pesadelo, desistiu no meio de tédio, ficou indiferente. Inclui reação FÍSICA e VISCERAL e a reação da PLATEIA.
- comparacoes: comparação com outro filme, outra obra, outro diretor, com o livro, com a franquia, com o trabalho anterior do mesmo autor.
- expectativa: o que a pessoa esperava ANTES de assistir e por quê — hype, recomendação de alguém, pressão de já ter ouvido falar, motivo de ter ido ver, expectativa frustrada ou superada.
- critica_social: crítica ao que o filme REPRESENTA ou faz socialmente — a mensagem, a ideologia, a política, a representação, o estúdio ou a franquia, o que a indústria está fazendo. Distinta de crítica ao que o filme É (isso é roteiro, ritmo, etc.).

REGRAS:
1. Atribua TODOS os eixos que a review realmente menciona, e SÓ esses. Uma review pode ter vários eixos, ou um só.
2. Só atribua um eixo se a review disser algo sobre ele. Nota alta ou entusiasmo genérico SEM descrever efeito nenhum ("obra-prima", "amei", "5 estrelas", "peak cinema") NÃO é impacto_emocional nem nenhum outro eixo — é elogio sem eixo. Mas um efeito DECLARADO é eixo mesmo dito em três palavras: "chorei", "não gostei", "odiei", "me deu sono", "passei mal", "ri alto" são impacto_emocional.
3. "livre" é sobre ASSUNTO, não sobre tamanho. Use "livre" quando a review fala de outra coisa que não o filme: a logística da sessão (legenda, dublagem, cinema, streaming, avião), a vida de quem escreveu, uma piada sobre outro assunto, um recado para outra pessoa. NÃO use "livre" só porque a review é curta ou diz pouco.
4. Sempre que incluir "livre", escreva em `temas_livres` de 1 a 2 rótulos curtos (2 a 4 palavras, em português, minúsculas) descrevendo o que não coube.
5. Uma review pode ter "livre" JUNTO com eixos: a parte que fala do filme vira eixo, a parte que não fala vira "livre". Devolva `["livre"]` sozinho só quando NADA na review fala do filme.
6. Review curta menciona POUCOS eixos, não ZERO eixos. Brevidade não é ausência de conteúdo. Uma frase seca sobre os personagens é roteiro_estrutura; um xingamento ao filme é impacto_emocional; uma piada cujo alvo é o enredo é roteiro_estrutura. Na dúvida entre atribuir o eixo que a review claramente toca e devolver "livre", atribua o eixo.
7. NÃO conte nada. NÃO some. NÃO comente. Devolva só o JSON.

Responda APENAS com um objeto JSON, sem cercas de código, exatamente neste formato:
{"eixos": ["..."], "temas_livres": ["..."]}"""


def taxonomia_id() -> str:
    """Identidade da taxonomia = hash do prompt + da lista de eixos.

    É o que impede uma sessão futura de reaproveitar, em silêncio,
    classificação feita sob outra definição de eixo. Mudou o prompt, mudou o
    id, e o arquivo de classificação antigo deixa de casar."""
    h = hashlib.sha256()
    h.update(SYSTEM.encode("utf-8"))
    h.update("|".join(EIXOS).encode("utf-8"))
    return h.hexdigest()[:12]


# O valor corrente, para quem precisa dele como constante (o schema de eixos
# carimba o veredito com ele, §2.5). Calculado, nunca digitado: um literal
# aqui poderia mentir sobre o prompt logo acima.
TAXONOMIA_ID = taxonomia_id()


def definicoes() -> dict[str, str]:
    """`{eixo: definição}`, EXTRAÍDAS do `SYSTEM` — não redigitadas.

    §[D3] precisa mostrar as definições ao rotulador. Copiá-las para uma
    segunda constante criaria duas verdades sobre o que é `tom_atmosfera`,
    e só uma delas entraria no `taxonomia_id`. Aqui a lista de eixos do
    prompt é a fonte, e o teste confere que os 10 saem.
    """
    fora: dict[str, str] = {}
    for linha in SYSTEM.splitlines():
        if not linha.startswith("- "):
            continue
        nome, _, definicao = linha[2:].partition(": ")
        if nome in EIXOS:
            fora[nome] = definicao.strip()
    return fora
