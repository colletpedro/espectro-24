"""Juiz v2 da checagem de apoio dos bullets: gpt-oss:20b, frase de prova, critério do dono.

**Por que existe (2026-10-19).** O juiz v1 (`checagem_bullets.py juiz`,
qwen3:14b) reprovou contra o rótulo do dono nos 40 pares: precisão 0,727
[0,558–0,849], recall 0,96. Diz "sim" demais (9 FP, 1 FN), mais no lado local
(6 FP) que no publicado (3 FP) — o que favorece o modelo pior —, e era o MESMO
modelo que escreveu o lado local. Este juiz vai ser a régua do fine-tuning, então
tem de ser confiável e a validação, honesta.

**O que muda em relação ao v1.**
1. Modelo: `gpt-oss:20b` (think=low), outro modelo que não o que escreveu o lado
   local, e o melhor que roda no notebook. Contexto: o menor que cabe no maior
   par dos 900 (ver `NUM_CTX_V2_0`), conferido por medição no Windows antes de rodar
   (`medir-contexto`) e por uma guarda em cada chamada.
2. Frase de prova: o modelo devolve `{"trecho": <a frase inteira da review>
   | null, "apoia": bool}`. O CÓDIGO decide (`apoio_final`): apoio = o modelo
   disse que apoia E o trecho não é nulo E tem ao menos 4 palavras E existe no
   texto da review (normalizando só espaços, caixa e a forma Unicode). Sem
   apoio, o motivo fica registrado (`motivo_sem_apoio`). O modelo não tem a
   palavra final.
3. Critério: o MESMO guia que o dono usou para rotular (`CRITERIO_DONO`).

**v2.2 (o 2º e último ajuste)** — estrutural: o juiz vê só o título, decide
em `"apoia_ideia_principal"` e precisa AFIRMAR `"evidencia_clara"`; a escolha
entre v2.1 e v2.2 é a pré-registrada (`escolha_pre_registrada`).

**v2.1 (o 1º ajuste, 2026-10-19)** — uma correção por causa de erro da v2.0:
o prompt destaca que o núcleo é o título e que apoio implícito inequívoco conta;
a comparação do trecho une as variantes tipográficas (`normalizar_v2_1`); e o
modelo devolve também `"ambiguo"`, e ambíguo nunca é apoio. Cada versão tem o seu
prompt, schema, janela e regra em `VERSOES`, e a v2.0 continua legível com o
hash dela.

**Calibração × validação.** Os 40 pares já rotulados servem para AJUSTAR o
prompt (no máximo 2 ajustes: `VERSOES` tem no máximo 3 entradas), nunca para
validá-lo — medir de novo nos mesmos 40 infla o resultado. O relatório de
`calibrar` diz isso no topo. A validação é numa amostra NOVA, depois de a versão
ser congelada (`CONGELADA`) e o hash dela (`config_sha256`) gravado no
REGISTRO.md antes da rotulagem nova.

Subcomandos (todos escrevem em `--dir`/juiz_v2, nunca em `resultado/`):

- `preparar` (Mac): grava a configuração da versão atual com o hash, a
  estimativa de contexto (cota conservadora) e a de tempo.
- `medir-contexto` (Windows): os maiores pares dos 900 com `num_ctx` folgado e
  1 token de saída — o `prompt_eval_count` exato. Sem medição que caiba, o
  `juiz` se recusa a rodar.
- `juiz --calibracao` (Windows): a versão atual nos 40 pares do rótulo antigo.
- `juiz --todos` (Windows): os 900 pares — só com a versão CONGELADA.
- `calibrar` (Mac): a calibração contra o rótulo do dono, por lado.
- `amostra-validacao` (Mac, depois de congelar): os 40 pares NOVOS, sem
  nenhum da calibração, e o documento cego para o dono rotular.
- `validar` (Mac): a versão congelada contra o rótulo novo, SÓ nos 40 novos.
- `relatorio` (Mac): a fidelidade dos bullets nos 900 com o juiz congelado;
  reprovado na validação, "ESTE RESULTADO NÃO VALE" na primeira linha.

Uso:
    python scripts/juiz_bullets_v2.py preparar --dir checagem-bullets
    python scripts/juiz_bullets_v2.py medir-contexto --dir checagem-bullets   # Windows
    python scripts/juiz_bullets_v2.py juiz --calibracao --dir checagem-bullets  # Windows
    python scripts/juiz_bullets_v2.py calibrar --dir checagem-bullets
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import inspect
import json
import math
import os
import re
import statistics
import sys
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

import checagem_bullets as C  # noqa: E402

DIR_V2 = Path("juiz_v2")
ESTAGIO = "juiz_bullets_v2"

# ===========================================================================
# Configuração — TUDO o que define o juiz entra em `config()` e no hash
# ===========================================================================

MODELO = "gpt-oss:20b"
# gpt-oss não desliga o raciocínio (`false` não vale para ele); `low` é o do gate.
THINK = "low"
# Teto de saída: raciocínio + JSON com o trecho. No gate do gpt-oss (think=low,
# 300 classificações) o `eval_count` teve mediana 130, p95 317 e máximo 696;
# 1024 dá 47% sobre o máximo. Estourar é falha registrada (`finish_reason`).
NUM_PREDICT = 1024
# Janela: o menor múltiplo de 512 que cabe o maior par dos 900 MAIS a saída.
# Cota conservadora (`estimar_contexto`): 0,35 token por caractere do prompt
# inteiro — no gate do gpt-oss a razão nunca passou de 0,343 em 417 prompts.
# Maior par (review de 4.990 caracteres, prompt de 6.998): ≤ 2.450 tokens +
# 1024 de saída = 3.474 → 3584. `medir-contexto` confere com a contagem exata
# do servidor antes de o juiz rodar, e cada chamada tem a guarda
# `contexto_estoura`. A janela é por versão (`num_ctx`): o prompt da v2.1 é
# mais longo.
NUM_CTX_V2_0 = 3584
# Semente fixa: a mesma entrada dá a mesma resposta na mesma máquina, e o par
# refeito depois de uma falha de rede não muda de veredito por sorteio. A
# temperatura fica a do modelo (a que o gate do gpt-oss usou), não fixada.
SEED = 20261019
# Ninguém sobrepõe a temperatura pelo ambiente: ela é parte da configuração.
VAR_TEMPERATURA = "ESPECTRO24_OLLAMA_TEMPERATURE"

# Medição de contexto: `num_ctx` folgado (o do gate, que cabe na memória do
# notebook) para o servidor contar o prompt inteiro sem truncar.
MEDICAO_NUM_CTX = 8192
MEDICAO_N_PARES = 10
RAZAO_TOKENS_POR_CHAR = 0.35

# Trecho com menos palavras que isto não é prova (apoio = falso, com o
# motivo): uma palavra solta existe em qualquer review do assunto, inclusive
# na de juízo oposto. Decisão do dono, 2026-10-19, antes de qualquer dado do v2.
MIN_PALAVRAS_TRECHO = 4

SCHEMA = {"type": "object",
          "properties": {"trecho": {"type": ["string", "null"]},
                         "apoia": {"type": "boolean"}},
          "required": ["trecho", "apoia"]}

# O guia que o dono usou para rotular (2026-10-19), sem mudar o sentido.
CRITERIO_DONO = """- **SIM** se a review conta como apoio para o bullet, NO MESMO SENTIDO. Apoio implícito conta, desde que sem ambiguidade. Review em outra língua conta.
- **NÃO** se a review fala do mesmo assunto com o juízo oposto (ex.: o bullet critica as atuações e a review as elogia).
- **NÃO** se a review atribui a opinião a outros e discorda dela (ex.: "dizem que é lento, mas não achei").
- **NÃO** se a review é ambivalente demais para servir de prova.
- **Bullet composto:** SIM se a review apoia o NÚCLEO do bullet, que é o título; NÃO se ela apoia só uma parte lateral (um detalhe da descrição, ou uma das ideias secundárias do título).
- **Na dúvida, NÃO.**
- Não julgue se o bullet é verdadeiro sobre o filme: julgue só se ESTA review o sustenta. Ignore quantas pessoas a descrição diz que concordam."""

SYSTEM_V2_0 = f"""Você confere se UMA review de cinema sustenta UM bullet de uma síntese.

O bullet resume algo que um grupo de reviews diria sobre o filme. Ele tem um TÍTULO, que é o núcleo do que o bullet afirma, e uma DESCRIÇÃO, que só ajuda a entender o título. A pergunta é só sobre ESTA review: ela conta como prova do que o bullet afirma?

Critério:
{CRITERIO_DONO}

Prova: em "trecho", copie da review a FRASE INTEIRA onde está a prova — a frase completa, do começo ao fim, não um fragmento nem palavras soltas —, LITERALMENTE, caractere por caractere, na língua original da review — sem traduzir, sem resumir, sem corrigir, sem juntar partes distantes. O trecho vai ser procurado no texto da review; se não for encontrado, ou se tiver menos de {MIN_PALAVRAS_TRECHO} palavras, a resposta não conta como apoio. Se a review não sustenta o bullet, "trecho" é null e "apoia" é false.

Responda APENAS com um objeto JSON: {{"trecho": "<trecho literal>" ou null, "apoia": true ou false}}."""

# A review PRIMEIRO e o bullet por último (como no v1): o system fica no KV
# do Ollama e a pergunta fica perto da resposta.
USER_V2_0 = ("Review (nota {nivel} de 5 estrelas):\n\n{texto}\n\n"
             "Bullet — título (o núcleo): {tema}\n"
             "Bullet — descrição: {exemplo}\n\n"
             "Esta review sustenta o bullet?")

# v2.1 — o primeiro ajuste (2026-10-19), uma correção por causa de erro da
# calibração da v2.0 (REGISTRO.md):
# 1. literalidade: 5 dos 8 FN foram o modelo exigindo menção explícita ou a
#    parte lateral do bullet → o prompt diz, com destaque e exemplos de filmes
#    FORA dos 40 pares, que o núcleo é o título, que a descrição é contexto e
#    que apoio implícito inequívoco conta;
# 2. cópia fiel com outro hífen (P28, U+2011) → `normalizar_v2_1`;
# 3. "na dúvida, não" pelo código (P15: o raciocínio dizia "ambíguo" e a
#    resposta foi sim) → o campo "ambiguo", e ambíguo nunca é apoio.
SCHEMA_V2_1 = {"type": "object",
               "properties": {"trecho": {"type": ["string", "null"]},
                              "ambiguo": {"type": "boolean"},
                              "apoia": {"type": "boolean"}},
               "required": ["trecho", "ambiguo", "apoia"]}

SYSTEM_V2_1 = f"""Você confere se UMA review de cinema sustenta UM bullet de uma síntese.

O bullet resume algo que um grupo de reviews diria sobre o filme. Ele tem um TÍTULO e uma DESCRIÇÃO. A pergunta é só sobre ESTA review: ela conta como prova do que o bullet afirma?

Critério:
{CRITERIO_DONO}

COMO LER O BULLET — IMPORTANTE:
- **O NÚCLEO do bullet é o TÍTULO.** A DESCRIÇÃO é contexto para entender o título, NÃO é exigência: a review NÃO precisa confirmar os detalhes da descrição (os exemplos, as nuances, quem acha o quê). Basta sustentar o título.
- **Apoio implícito CONTA, desde que inequívoco.** A review não precisa usar as palavras do bullet nem nomear o aspecto. Exemplos, de outros filmes:
  - bullet "Atuação de Cate Blanchett"; review "Cate Blanchett é uma força da natureza, não consegui tirar os olhos dela" → SIM: elogiar a protagonista é elogiar a atuação.
  - bullet "Romance ocupa espaço demais"; review "metade do filme é a vida amorosa do piloto, eu queria ver as corridas" → SIM: reclamar do excesso de vida pessoal sustenta o foco excessivo no relacionamento, mesmo sem nomear o par.
- **Título com duas ideias** (ex.: "Fotografia deslumbrante e trilha marcante"): basta a review apoiar a ideia PRINCIPAL, a que dá o assunto do bullet — "cada plano parece uma pintura" → SIM, mesmo sem falar da trilha. Apoiar só a ideia secundária ("a trilha é boa") → NÃO.
- Isto não afrouxa o resto do critério: juízo oposto, opinião atribuída a outros e review ambivalente continuam NÃO.

Ambiguidade: em "ambiguo", responda true se a leitura da review a favor do bullet NÃO é inequívoca — se ela pode ser lida dos dois jeitos, se é morna ou dividida sobre o assunto, ou se você mesmo hesitou ("talvez", "possivelmente", "ambíguo"). Resposta com "ambiguo": true não conta como apoio. Apoio implícito mas claro NÃO é ambíguo.

Prova: em "trecho", copie da review a FRASE INTEIRA onde está a prova — a frase completa, do começo ao fim, não um fragmento nem palavras soltas —, LITERALMENTE, caractere por caractere, na língua original da review — sem traduzir, sem resumir, sem corrigir, sem juntar partes distantes. **Não omita nem altere NADA**: nenhuma palavra, nem interjeição, palavrão, gíria ou erro de digitação; não use reticências para pular partes. O trecho vai ser procurado no texto da review; se não for encontrado, ou se tiver menos de {MIN_PALAVRAS_TRECHO} palavras, a resposta não conta como apoio. Se a review não sustenta o bullet, "trecho" é null e "apoia" é false.

Responda APENAS com um objeto JSON: {{"trecho": "<trecho literal>" ou null, "ambiguo": true ou false, "apoia": true ou false}}."""

# Janela da v2.1: a mesma conta da v2.0 (`estimar_contexto`) com o prompt mais
# longo — o maior par passa de 3.584; o menor múltiplo de 512 que cabe é 4096.
NUM_CTX_V2_1 = 4096

# v2.2 — o último ajuste (2026-10-19). A v2.1 errou quase só no lado
# PUBLICADO (recall 0,71 × 0,91 no local), e os erros vinham do modelo NÃO
# obedecer ao texto do prompt (P11, P28, P40 contrariam a instrução; "ambiguo"
# nunca disparou, nem com "it's ambiguous" no raciocínio). Por isso as mudanças
# são ESTRUTURAIS, não mais prosa:
# 1. o juiz vê SÓ o título (`USER_V2_2` não tem a descrição), pois a v2.1
#    seguiu cobrando a descrição (P29);
# 2. o campo de decisão é "apoia_ideia_principal" (em título com duas ideias,
#    a primeira) — sai o "apoia" genérico;
# 3. polaridade invertida: "evidencia_clara" tem de ser AFIRMADA verdadeira
#    (sai "ambiguo"). Normalização, frase inteira e modelo: os da v2.1.
SCHEMA_V2_2 = {"type": "object",
               "properties": {"trecho": {"type": ["string", "null"]},
                              "apoia_ideia_principal": {"type": "boolean"},
                              "evidencia_clara": {"type": "boolean"}},
               "required": ["trecho", "apoia_ideia_principal", "evidencia_clara"]}

SYSTEM_V2_2 = f"""Você confere se UMA review de cinema sustenta o TÍTULO de UM bullet de uma síntese.

O bullet resume algo que um grupo de reviews diria sobre o filme. Você recebe só o TÍTULO do bullet, que é o núcleo do que ele afirma. A pergunta é só sobre ESTA review: ela conta como prova da IDEIA PRINCIPAL do título?

Critério:
{CRITERIO_DONO}

A IDEIA PRINCIPAL: se o título tem uma ideia só, é ela. Se tem duas ideias (ex.: "Fotografia deslumbrante e trilha marcante"), é a PRIMEIRA — aqui, a fotografia. A review não precisa falar da segunda.

A review não precisa usar as palavras do título nem nomear o aspecto: apoio implícito conta, desde que inequívoco. Exemplos, de outros filmes:
- título "Atuação de Cate Blanchett"; review "Cate Blanchett é uma força da natureza, não consegui tirar os olhos dela" → apoia: elogiar a protagonista é elogiar a atuação.
- título "Romance ocupa espaço demais"; review "metade do filme é a vida amorosa do piloto, eu queria ver as corridas" → apoia: reclamar do excesso de vida pessoal sustenta o foco excessivo no relacionamento, mesmo sem nomear o par.
- título "Fotografia deslumbrante e trilha marcante"; review "cada plano parece uma pintura" → apoia; review que só elogia a trilha → não apoia.

Os campos:
- "apoia_ideia_principal": true se a review sustenta a ideia principal do título, no mesmo sentido.
- "evidencia_clara": true SÓ se você AFIRMA que a prova é clara — o trecho, lido na review, sustenta a ideia principal sem precisar de suposição. Se a review é ambígua, morna, dividida, se fala do assunto sem tomar o mesmo lado, ou se você hesitou ("talvez", "possivelmente", "ambíguo"), é false. Sem evidência clara afirmada, a resposta não conta como apoio.
- "trecho": copie da review a FRASE INTEIRA onde está a prova — a frase completa, do começo ao fim, não um fragmento nem palavras soltas —, LITERALMENTE, caractere por caractere, na língua original da review — sem traduzir, sem resumir, sem corrigir, sem juntar partes distantes. **Não omita nem altere NADA**: nenhuma palavra, nem interjeição, palavrão, gíria ou erro de digitação; não use reticências para pular partes. O trecho vai ser procurado no texto da review; se não for encontrado, ou se tiver menos de {MIN_PALAVRAS_TRECHO} palavras, a resposta não conta como apoio. Se a review não sustenta a ideia principal, "trecho" é null e os dois campos são false.

Responda APENAS com um objeto JSON: {{"trecho": "<trecho literal>" ou null, "apoia_ideia_principal": true ou false, "evidencia_clara": true ou false}}."""

# Sem a descrição: o juiz não tem como cobrá-la.
USER_V2_2 = ("Review (nota {nivel} de 5 estrelas):\n\n{texto}\n\n"
             "Título do bullet: {tema}\n\n"
             "Esta review sustenta a ideia principal do título?")

NUM_CTX_V2_2 = 4096

# Critério de aprovação (o de antes, mais a diferença entre os lados): um
# juiz que erra mais num lado não serve para compará-los.
CRITERIO_V2 = {"precisao_min": 0.8, "recall_min": 0.8, "dif_precisao_lados_max": 0.15}


# ===========================================================================
# Frase de prova — a regra é do código
# ===========================================================================

def normalizar(s: str) -> str:
    """Só espaços, caixa e forma Unicode (NFC): nada de tirar acento,
    pontuação ou aspas — o trecho tem de ser literal."""
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", s).casefold()).strip()


def trecho_encontrado(trecho: str | None, texto: str) -> bool:
    """O trecho existe no texto da review? Trecho nulo ou vazio não existe
    (vazio estaria "dentro" de qualquer texto)."""
    if trecho is None:
        return False
    t = normalizar(trecho)
    return bool(t) and t in normalizar(texto)


def n_palavras(trecho: str | None) -> int:
    """Palavras = pedaços separados por espaço, depois de `normalizar`."""
    return len(normalizar(trecho).split()) if trecho else 0


def motivo_sem_apoio(apoia: bool, trecho: str | None, texto: str) -> str | None:
    """Por que NÃO há apoio (`None` = há). A ordem é a da regra: o modelo
    disse que não apoia; não deu trecho; o trecho é curto demais para ser
    prova (uma palavra como "acting" existe em "Great acting" e sustentaria
    "atuações insuficientes"); o trecho não está na review."""
    if not apoia:
        return "modelo disse que não apoia"
    if trecho is None or not normalizar(trecho):
        return "trecho nulo"
    n = n_palavras(trecho)
    if n < MIN_PALAVRAS_TRECHO:
        return f"trecho curto ({n} palavra{'s' if n != 1 else ''} < {MIN_PALAVRAS_TRECHO})"
    if not trecho_encontrado(trecho, texto):
        return "trecho não encontrado na review"
    return None


def apoio_final(apoia: bool, trecho: str | None, texto: str) -> bool:
    """A regra final, aplicada pelo código e não pelo modelo: apoia E trecho
    não-nulo E com ao menos `MIN_PALAVRAS_TRECHO` palavras E achado na review."""
    return motivo_sem_apoio(apoia, trecho, texto) is None


def ler_resposta(texto: str) -> dict:
    """`{"trecho": str|null, "apoia": bool}` e nada além — qualquer outra
    forma é falha (o par fica sem veredito)."""
    dados = json.loads(texto)
    if not isinstance(dados, dict) or set(dados) != {"trecho", "apoia"}:
        raise ValueError(f"resposta fora do formato: {texto[:200]!r}")
    if not isinstance(dados["apoia"], bool):
        raise ValueError(f"apoia não é booleano: {texto[:200]!r}")
    if dados["trecho"] is not None and not isinstance(dados["trecho"], str):
        raise ValueError(f"trecho não é texto nem null: {texto[:200]!r}")
    return {"trecho": dados["trecho"], "apoia": dados["apoia"]}


# A regra da v2.1. As funções acima são a da v2.0 e não mudam: o hash
# a42f4893… é o fonte delas, e os registros da v2.0 continuam legíveis.

# Variantes tipográficas que viram a forma simples antes do NFKC: hífens e
# travessões → "-", aspas → '"', apóstrofos e acentos soltos → "'", e os
# caracteres de largura zero somem (os espaços especiais o NFKC e o `\s` já unem).
TIPOGRAFIA_V2_1 = {
    **dict.fromkeys("‐‑‒–—―−⁃﹘﹣－", "-"),
    **dict.fromkeys("“”„‟«»″‶＂", '"'),
    **dict.fromkeys("‘’‚‛′‵´`＇", "'"),
    **dict.fromkeys("​‌‍⁠﻿", ""),
}
_TABELA_V2_1 = str.maketrans(TIPOGRAFIA_V2_1)


def normalizar_v2_1(s: str) -> str:
    """A da v2.0 mais a tipografia (`TIPOGRAFIA_V2_1`) e NFKC no lugar de NFC.
    Letra ou palavra diferente continua diferente: cópia com palavra omitida,
    ou com "…" no lugar de partes distantes, segue não encontrada."""
    s = unicodedata.normalize("NFKC", s.translate(_TABELA_V2_1))
    return re.sub(r"\s+", " ", s.casefold()).strip()


def trecho_encontrado_v2_1(trecho: str | None, texto: str) -> bool:
    if trecho is None:
        return False
    t = normalizar_v2_1(trecho)
    return bool(t) and t in normalizar_v2_1(texto)


def n_palavras_v2_1(trecho: str | None) -> int:
    return len(normalizar_v2_1(trecho).split()) if trecho else 0


def motivo_sem_apoio_v2_1(resp: dict, texto: str) -> str | None:
    """A da v2.0 com o "na dúvida, não" do código: o modelo disse que é
    ambíguo → não há apoio, diga ele o que disser em "apoia"."""
    if not resp["apoia"]:
        return "modelo disse que não apoia"
    if resp["ambiguo"]:
        return "modelo disse que é ambíguo"
    trecho = resp["trecho"]
    if trecho is None or not normalizar_v2_1(trecho):
        return "trecho nulo"
    n = n_palavras_v2_1(trecho)
    if n < MIN_PALAVRAS_TRECHO:
        return f"trecho curto ({n} palavra{'s' if n != 1 else ''} < {MIN_PALAVRAS_TRECHO})"
    if not trecho_encontrado_v2_1(trecho, texto):
        return "trecho não encontrado na review"
    return None


def ler_resposta_v2_1(texto: str) -> dict:
    """`{"trecho": str|null, "ambiguo": bool, "apoia": bool}` e nada além."""
    dados = json.loads(texto)
    if not isinstance(dados, dict) or set(dados) != {"trecho", "ambiguo", "apoia"}:
        raise ValueError(f"resposta fora do formato: {texto[:200]!r}")
    for campo in ("ambiguo", "apoia"):
        if not isinstance(dados[campo], bool):
            raise ValueError(f"{campo} não é booleano: {texto[:200]!r}")
    if dados["trecho"] is not None and not isinstance(dados["trecho"], str):
        raise ValueError(f"trecho não é texto nem null: {texto[:200]!r}")
    return {"trecho": dados["trecho"], "ambiguo": dados["ambiguo"], "apoia": dados["apoia"]}


def motivo_sem_apoio_v2_2(resp: dict, texto: str) -> str | None:
    """Apoio = apoia a ideia principal E evidência clara AFIRMADA E trecho
    válido (a normalização e a contagem de palavras são as da v2.1)."""
    if not resp["apoia_ideia_principal"]:
        return "modelo disse que não apoia a ideia principal"
    if not resp["evidencia_clara"]:
        return "modelo não afirmou evidência clara"
    trecho = resp["trecho"]
    if trecho is None or not normalizar_v2_1(trecho):
        return "trecho nulo"
    n = n_palavras_v2_1(trecho)
    if n < MIN_PALAVRAS_TRECHO:
        return f"trecho curto ({n} palavra{'s' if n != 1 else ''} < {MIN_PALAVRAS_TRECHO})"
    if not trecho_encontrado_v2_1(trecho, texto):
        return "trecho não encontrado na review"
    return None


def ler_resposta_v2_2(texto: str) -> dict:
    """`{"trecho": str|null, "apoia_ideia_principal": bool, "evidencia_clara":
    bool}` e nada além."""
    campos = ("apoia_ideia_principal", "evidencia_clara")
    dados = json.loads(texto)
    if not isinstance(dados, dict) or set(dados) != {"trecho", *campos}:
        raise ValueError(f"resposta fora do formato: {texto[:200]!r}")
    for campo in campos:
        if not isinstance(dados[campo], bool):
            raise ValueError(f"{campo} não é booleano: {texto[:200]!r}")
    if dados["trecho"] is not None and not isinstance(dados["trecho"], str):
        raise ValueError(f"trecho não é texto nem null: {texto[:200]!r}")
    return {"trecho": dados["trecho"], **{c: dados[c] for c in campos}}


# ===========================================================================
# Versões
# ===========================================================================

# Uma entrada por versão; versão nova nunca reescreve a anterior. Cada uma
# leva o seu prompt, schema, janela e regra (`regra` e `regra_dados` entram no
# hash). No máximo 2 ajustes depois da v2.0 (pedido do dono, 2026-10-19).
VERSOES = {
    "v2.0": {"system": SYSTEM_V2_0, "user": USER_V2_0, "schema": SCHEMA,
             "num_ctx": NUM_CTX_V2_0,
             "regra": (normalizar, trecho_encontrado, n_palavras, motivo_sem_apoio,
                       apoio_final, ler_resposta),
             "ler": ler_resposta, "encontrado": trecho_encontrado, "palavras": n_palavras,
             "motivo": lambda r, texto: motivo_sem_apoio(r["apoia"], r["trecho"], texto),
             "nota": "primeira versão: critério do dono, frase de prova; sem ajuste"},
    "v2.1": {"system": SYSTEM_V2_1, "user": USER_V2_0, "schema": SCHEMA_V2_1,
             "num_ctx": NUM_CTX_V2_1,
             "regra": (normalizar_v2_1, trecho_encontrado_v2_1, n_palavras_v2_1,
                       motivo_sem_apoio_v2_1, ler_resposta_v2_1),
             "regra_dados": [json.dumps(TIPOGRAFIA_V2_1, sort_keys=True)],
             "ler": ler_resposta_v2_1, "encontrado": trecho_encontrado_v2_1,
             "palavras": n_palavras_v2_1, "motivo": motivo_sem_apoio_v2_1,
             "nota": "1º ajuste: núcleo/implícito no prompt, normalização tipográfica, "
                     "campo ambiguo"},
    "v2.2": {"system": SYSTEM_V2_2, "user": USER_V2_2, "schema": SCHEMA_V2_2,
             "num_ctx": NUM_CTX_V2_2, "decisao": "apoia_ideia_principal",
             "regra": (normalizar_v2_1, trecho_encontrado_v2_1, n_palavras_v2_1,
                       motivo_sem_apoio_v2_2, ler_resposta_v2_2),
             "regra_dados": [json.dumps(TIPOGRAFIA_V2_1, sort_keys=True)],
             "ler": ler_resposta_v2_2, "encontrado": trecho_encontrado_v2_1,
             "palavras": n_palavras_v2_1, "motivo": motivo_sem_apoio_v2_2,
             "nota": "2º e último ajuste: só o título, apoia_ideia_principal, "
                     "evidencia_clara afirmada"},
}
MAX_VERSOES = 3
VERSAO_ATUAL = "v2.2"
# A versão congelada para a validação na amostra nova e os 900 pares — `None`
# até a calibração terminar. Congelar = fixar aqui E gravar `config_sha256` no
# REGISTRO.md antes de qualquer rotulagem nova.
# Congelada em 2026-10-20 pela regra pré-registrada (a v2.2 passou nos três
# critérios na calibração); o hash está no REGISTRO.md desde antes da
# rotulagem nova.
CONGELADA: str | None = "v2.2"


# ===========================================================================
# Configuração e hash
# ===========================================================================

def _versao(versao: str) -> dict:
    if versao not in VERSOES:
        raise ValueError(f"versão {versao!r} não existe (há {list(VERSOES)})")
    return VERSOES[versao]


def num_ctx(versao: str = VERSAO_ATUAL) -> int:
    return _versao(versao)["num_ctx"]


def schema(versao: str = VERSAO_ATUAL) -> dict:
    return _versao(versao)["schema"]


def motivo_da_versao(resp: dict, texto: str, versao: str = VERSAO_ATUAL) -> str | None:
    """Por que não há apoio na regra da versão (`None` = há)."""
    return _versao(versao)["motivo"](resp, texto)


def system(versao: str = VERSAO_ATUAL) -> str:
    return _versao(versao)["system"]


def user(par: dict, versao: str = VERSAO_ATUAL) -> str:
    return _versao(versao)["user"].format(nivel=par["nivel"], texto=par["texto"],
                                          tema=par["tema"], exemplo=par["exemplo"])


def config(versao: str = VERSAO_ATUAL) -> dict:
    """Tudo o que define o juiz: prompt, modelo, parâmetros e a regra do
    código (o fonte das funções que decidem o apoio)."""
    v = _versao(versao)
    regra = "\n".join([inspect.getsource(f) for f in v["regra"]] + v.get("regra_dados", []))
    return {"versao": versao, "modelo": MODELO, "think": THINK, "num_ctx": v["num_ctx"],
            "min_palavras_trecho": MIN_PALAVRAS_TRECHO,
            "num_predict": NUM_PREDICT, "seed": SEED, "temperatura": "padrão do modelo",
            "schema": v["schema"], "system": v["system"], "user_template": v["user"],
            "regra_sha256": C._sha256_texto(regra)}


def config_sha256(versao: str = VERSAO_ATUAL) -> str:
    return C._sha256_texto(json.dumps(config(versao), sort_keys=True, ensure_ascii=False))


# ===========================================================================
# Contexto
# ===========================================================================

def chars_do_prompt(par: dict, versao: str = VERSAO_ATUAL) -> int:
    return len(system(versao)) + len(user(par, versao))


def estimar_contexto(pares: list[dict], versao: str = VERSAO_ATUAL) -> dict:
    """Cota CONSERVADORA (não medição): tokens ≤ 0,35 × caracteres do prompt
    inteiro. A janela tem de caber o prompt e a saída."""
    maior = max(pares, key=lambda p: chars_do_prompt(p, versao))
    ch = chars_do_prompt(maior, versao)
    cota = math.ceil(RAZAO_TOKENS_POR_CHAR * ch)
    precisa = cota + NUM_PREDICT
    return {"maior_id_par": maior["id_par"], "maior_chars_review": len(maior["texto"]),
            "maior_chars_prompt": ch, "cota_tokens_prompt": cota,
            "num_predict": NUM_PREDICT, "precisa": precisa,
            "menor_multiplo_512": 512 * math.ceil(precisa / 512),
            "num_ctx": num_ctx(versao), "cabe": precisa <= num_ctx(versao)}


def maiores_pares(pares: list[dict], n: int = MEDICAO_N_PARES,
                  versao: str = VERSAO_ATUAL) -> list[dict]:
    """Os `n` pares de prompt mais longo, uma review por vez (o mesmo texto
    com outro bullet quase não muda a conta)."""
    fora, vistas = [], set()
    for p in sorted(pares, key=lambda p: (-chars_do_prompt(p, versao), p["id_par"])):
        chave = (p["slug"], p["review_id"])
        if chave not in vistas:
            vistas.add(chave)
            fora.append(p)
        if len(fora) == n:
            break
    return fora


def julgar_medicao(medidos: list[dict], versao: str = VERSAO_ATUAL) -> dict:
    mx = max(m["prompt_eval_count"] for m in medidos)
    precisa, ctx = mx + NUM_PREDICT, num_ctx(versao)
    return {"max_prompt_tokens": mx, "num_predict": NUM_PREDICT, "precisa": precisa,
            "num_ctx": ctx, "folga": ctx - precisa, "cabe": precisa <= ctx,
            "menor_multiplo_512": 512 * math.ceil(precisa / 512)}


def contexto_estoura(resp: dict, versao: str = VERSAO_ATUAL) -> str | None:
    """A guarda por chamada: prompt + saída têm de caber na janela, e o
    prompt tem de deixar a saída inteira. Um prompt truncado pelo servidor
    também cai aqui (a contagem dele encosta na janela)."""
    pe, ev = int(resp.get("prompt_eval_count") or 0), int(resp.get("eval_count") or 0)
    ctx = num_ctx(versao)
    if pe > ctx - NUM_PREDICT or pe + ev > ctx:
        return (f"contexto: prompt {pe} + saída {ev} tokens não cabe com folga em "
                f"num_ctx={ctx} (num_predict={NUM_PREDICT})")
    return None


# ===========================================================================
# Execução
# ===========================================================================

CAMPOS_RESP = ("modelo_efetivo", "think", "finish_reason", "latencia_s", "leitura_prompt_s",
               "geracao_s", "carga_s", "prompt_eval_count", "eval_count", "custo_usd")


def rodar(pares: list[dict], saida: Path, chamar, *, versao: str,
          progresso_a_cada: int = 10) -> dict:
    """Uma chamada por par, EM SEQUÊNCIA, anexando um registro por chamada;
    par com `ok: true` desta MESMA configuração não é refeito. `chamar(system,
    user) -> dict` no formato de `local_ollama.resposta_json_local`."""
    sha = config_sha256(versao)
    feitos = {r["id_par"] for r in C._ler_jsonl(saida)
              if r.get("ok") and r.get("config_sha256") == sha}
    pendentes = [p for p in pares if p["id_par"] not in feitos]
    print(f"  juiz v2 {versao}: {len(feitos)} feitos · {len(pendentes)} pendentes", flush=True)
    C.exigir_fora_de_resultado(saida)
    saida.parent.mkdir(parents=True, exist_ok=True)
    sys_txt = system(versao)
    t0, n_falhas = time.time(), 0
    with saida.open("a", encoding="utf-8") as fh:
        for j, p in enumerate(pendentes, 1):
            base = {"id_par": p["id_par"], "versao": versao, "config_sha256": sha,
                    "modelo": MODELO,
                    "ts": datetime.now(timezone.utc).isoformat(timespec="seconds")}
            resp = None
            try:
                resp = chamar(sys_txt, user(p, versao))
                if resp.get("finish_reason") != "stop":
                    raise ValueError(f"finish_reason={resp.get('finish_reason')!r} "
                                     f"(teto de {NUM_PREDICT} tokens?)")
                estouro = contexto_estoura(resp, versao)
                if estouro:
                    raise ValueError(estouro)
                lida = _versao(versao)["ler"](resp["texto"])
                # o apoio do código, para quem lê o registro; a leitura
                # (`vereditos`) recalcula do texto e não confia neste campo
                reg = {"ok": True, **base, **lida,
                       "motivo_sem_apoio": motivo_da_versao(lida, p["texto"], versao)}
            except Exception as e:  # noqa: BLE001
                n_falhas += 1
                reg = {"ok": False, **base, "erro": f"{type(e).__name__}: {e}",
                       "latencia_s": getattr(e, "latencia_s", None)}
                if resp is not None:
                    reg["resposta_crua"] = resp.get("texto")
            if resp is not None:
                reg.update({k: resp[k] for k in CAMPOS_RESP if k in resp})
                reg["pensamento"] = resp.get("pensamento")
            fh.write(json.dumps(reg, ensure_ascii=False) + "\n")
            fh.flush()
            if j % progresso_a_cada == 0 or j == len(pendentes):
                dt = time.time() - t0
                resta = dt / j * (len(pendentes) - j)
                print(f"    {j}/{len(pendentes)} · {dt / 60:.1f} min · "
                      f"falhas {n_falhas} · faltam ~{resta / 60:.0f} min", flush=True)
    return {"feitos_antes": len(feitos), "rodados": len(pendentes), "falhas": n_falhas,
            "parede_s": round(time.time() - t0, 1)}


def vereditos(pares: list[dict], regs: list[dict], versao: str) -> dict[str, dict]:
    """`{id_par: {...}}` com o apoio FINAL, recalculado aqui do trecho e do
    texto da review (o registro guarda só o que o modelo disse). Exige um
    veredito por par, todos desta configuração, do modelo e do nível de
    raciocínio pedidos: par sem veredito não vira "não" em silêncio."""
    sha = config_sha256(versao)
    texto = {p["id_par"]: p["texto"] for p in pares}
    fora: dict[str, dict] = {}
    for r in regs:
        if not r.get("ok"):
            continue
        if r.get("config_sha256") != sha:
            raise ValueError(f"{r['id_par']}: julgado com outra configuração "
                             f"({r.get('config_sha256')}) — o arquivo mistura "
                             f"configurações; mova-o e rode o juiz de novo")
        if r.get("modelo_efetivo") != MODELO or r.get("think") != THINK:
            raise ValueError(f"{r['id_par']}: modelo {r.get('modelo_efetivo')!r} / think "
                             f"{r.get('think')!r} — o juiz v2 é {MODELO} com think={THINK}")
        if r["id_par"] not in texto:
            raise ValueError(f"veredito de par que não está na entrada: {r['id_par']}")
        tx, v = texto[r["id_par"]], _versao(versao)
        lida = {k: r[k] for k in v["schema"]["required"]}
        mot = motivo_da_versao(lida, tx, versao)
        fora[r["id_par"]] = {"apoia_modelo": lida[v.get("decisao", "apoia")],
                             "ambiguo": lida.get("ambiguo"),
                             "evidencia_clara": lida.get("evidencia_clara"),
                             "trecho": r["trecho"],
                             "trecho_palavras": v["palavras"](r["trecho"]),
                             "trecho_encontrado": v["encontrado"](r["trecho"], tx),
                             "apoio": mot is None,
                             "motivo": mot, "pensamento": r.get("pensamento")}
    faltam = [p["id_par"] for p in pares if p["id_par"] not in fora]
    if faltam:
        raise ValueError(f"{len(faltam)} pares sem veredito do juiz v2 (ex.: {faltam[:2]}) "
                         f"— rode `juiz` de novo: ele refaz só os que faltam")
    return fora


# ===========================================================================
# Calibração (os 40 pares antigos) e critério
# ===========================================================================

# Os pares que o dono marcou como duvidosos na rotulagem (REGISTRO.md,
# 2026-10-19). O rótulo não muda; servem para ler os erros.
DUVIDOSOS_CALIBRACAO = ("P03", "P09", "P11", "P13", "P15", "P22", "P28", "P34", "P36", "P39")


def mapa_conferido(d: Path) -> dict:
    mapa = C._ler_json(d / C.ARQ_MAPA)
    selo = C._sha256_texto(json.dumps({k: mapa[k] for k in ("semente", "pares")},
                                      sort_keys=True, ensure_ascii=False))
    if selo != mapa["sha256"]:
        raise SystemExit("o mapeamento da rotulagem não confere com o próprio selo")
    return mapa


def pares_calibracao(d: Path) -> list[dict]:
    """Os 40 pares do rótulo antigo, na ordem da entrada (agrupados por
    review, como o juiz v1 rodou)."""
    ids = set(mapa_conferido(d)["pares"].values())
    pares = [p for p in C._ler_jsonl(d / C.ARQ_ENTRADA) if p["id_par"] in ids]
    if len(pares) != len(ids):
        raise SystemExit(f"{len(ids) - len(pares)} pares do mapa não estão na entrada")
    return pares


def julgar(geral: dict, por_lado: dict, criterio: dict = CRITERIO_V2) -> dict:
    """Precisão e recall mínimos no geral E a precisão dos dois lados a no
    máximo `dif_precisao_lados_max` uma da outra. Lado sem precisão (o juiz
    não disse sim nenhuma vez nele) reprova: não há como comparar."""
    motivos = list(C.julgar_validacao(geral, criterio)["motivos"])
    ps = {lado: por_lado[lado]["precisao"] for lado in C.LADOS}
    if any(v is None for v in ps.values()):
        motivos.append(f"precisão indefinida num lado ({ps})")
        dif = None
    else:
        dif = round(abs(ps["local"] - ps["publicado"]), 3)
        if dif > criterio["dif_precisao_lados_max"]:
            motivos.append(f"precisão difere {dif} entre os lados "
                           f"(> {criterio['dif_precisao_lados_max']})")
    return {"vale": not motivos, "motivos": motivos, "criterio": criterio,
            "dif_precisao_lados": dif}


# A regra de escolha entre a v2.1 e a v2.2, PRÉ-REGISTRADA no REGISTRO.md
# (2026-10-19) antes de a v2.2 rodar: a v2.2 passa nos três critérios →
# congela a v2.2; senão, a de MAIOR recall no pior lado (o defeito da v2.1 era
# negar apoio a bullets bons de um lado só); empate → v2.1. Os 40 pares novos
# não são tocados por nenhuma das duas antes da escolha.
def escolha_pre_registrada(comparacao: dict) -> dict:
    if comparacao["v2.2"]["julgamento"]["vale"]:
        return {"congelar": "v2.2", "motivo": "a v2.2 passa nos três critérios"}
    pior = {v: min(comparacao[v]["por_lado"][lado]["recall"] for lado in C.LADOS)
            for v in ("v2.1", "v2.2")}
    if pior["v2.2"] > pior["v2.1"]:
        return {"congelar": "v2.2", "recall_pior_lado": pior,
                "motivo": "a v2.2 não passa nos três critérios, mas tem o maior recall "
                          "no pior lado"}
    return {"congelar": "v2.1", "recall_pior_lado": pior,
            "motivo": "a v2.2 não passa nos três critérios e não tem recall maior no "
                      "pior lado" + (" (empate → v2.1)" if pior["v2.2"] == pior["v2.1"]
                                     else "")}


def calibracao(d: Path, versao: str) -> dict:
    """A versão contra o rótulo do dono, ao lado do v1 e das versões v2
    anteriores que já rodaram (cada uma lida com a própria regra)."""
    mapa = mapa_conferido(d)
    pares = pares_calibracao(d)
    ver = vereditos(pares, C._ler_jsonl(d / DIR_V2 / f"calibracao_{versao}_saida.jsonl"),
                    versao)
    anteriores = {}
    for vv in list(VERSOES)[:list(VERSOES).index(versao)]:
        arq = d / DIR_V2 / f"calibracao_{vv}_saida.jsonl"
        if arq.exists():
            anteriores[vv] = vereditos(pares, C._ler_jsonl(arq), vv)
    dono = C.ler_rotulos(d / C.ARQ_ROTULOS, list(mapa["pares"]))
    v1 = C.vereditos(C._ler_jsonl(d / C.ARQ_ENTRADA), C._ler_jsonl(d / C.ARQ_SAIDA))
    por_par = {p["id_par"]: p for p in pares}
    linhas = []
    for par, id_par in mapa["pares"].items():
        p, v = por_par[id_par], ver[id_par]
        linhas.append({"par": par, "id_par": id_par, "lado": p["lado"], "slug": p["slug"],
                       "bucket": p["bucket"], "tema": p["tema"], "dono": dono[par],
                       "juiz": v["apoio"], "juiz_v1": v1[id_par],
                       "juiz_anteriores": {vv: a[id_par]["apoio"] for vv, a in anteriores.items()},
                       "apoia_modelo": v["apoia_modelo"], "ambiguo": v["ambiguo"],
                       "evidencia_clara": v["evidencia_clara"],
                       "trecho": v["trecho"], "trecho_encontrado": v["trecho_encontrado"],
                       "trecho_palavras": v["trecho_palavras"], "motivo": v["motivo"],
                       "duvidoso": par in DUVIDOSOS_CALIBRACAO,
                       "pensamento": v["pensamento"]})

    def medir(juiz) -> dict:
        geral = C.matriz([(x["dono"], juiz(x)) for x in linhas])
        por_lado = {lado: C.matriz([(x["dono"], juiz(x)) for x in linhas if x["lado"] == lado])
                    for lado in C.LADOS}
        return {"geral": geral, "por_lado": por_lado, "julgamento": julgar(geral, por_lado)}

    atual = medir(lambda x: x["juiz"])
    comparacao = {"v1": medir(lambda x: x["juiz_v1"]),
                  **{vv: medir(lambda x, vv=vv: x["juiz_anteriores"][vv]) for vv in anteriores},
                  versao: atual}
    escolha = (escolha_pre_registrada(comparacao)
               if versao == "v2.2" and "v2.1" in comparacao else None)
    return {"versao": versao, "config_sha256": config_sha256(versao),
            "selo_mapa": mapa["sha256"], "escolha": escolha, "geral": atual["geral"],
            "por_lado": atual["por_lado"], "v1": comparacao["v1"],
            "comparacao": comparacao, "julgamento": atual["julgamento"],
            "derrubados_pelo_codigo": [{"par": x["par"], "motivo": x["motivo"]}
                                       for x in linhas if x["apoia_modelo"] and not x["juiz"]],
            "erros": [x["par"] for x in linhas if x["dono"] != x["juiz"]],
            "pares": linhas}


def md_calibracao(cal: dict) -> str:
    def linha(nome, m):
        return (f"| {nome} | {m['n']} | {m['vp']} | {m['fp']} | {m['fn']} | {m['vn']} | "
                f"{m['precisao']} {m['precisao_ic95']} | {m['recall']} {m['recall_ic95']} |")

    def sn(b):
        return "sim" if b else "não"
    j, comp = cal["julgamento"], cal["comparacao"]
    L = [f"# Calibração do juiz v2 — versão {cal['versao']}", "",
         "> **CALIBRAÇÃO, NÃO VALIDAÇÃO.** Estes 40 pares são os mesmos usados para "
         "ajustar o prompt; o número aqui é otimista por construção. O juiz só vale "
         "depois de congelado e medido numa amostra NOVA.", "",
         f"Configuração `{cal['config_sha256']}` · {MODELO} think={THINK} · "
         f"num_ctx {num_ctx(cal['versao'])} · num_predict {NUM_PREDICT} · seed {SEED}", "",
         ("No critério proposto (a pré-registrar antes da amostra nova), esta "
          "calibração passaria" if j["vale"] else
          "No critério proposto (a pré-registrar antes da amostra nova), esta "
          "calibração REPROVARIA: " + "; ".join(j["motivos"]))
         + f" — precisão e recall ≥ 0,8; diferença de precisão entre os lados ≤ "
         f"{CRITERIO_V2['dif_precisao_lados_max']}; diferença medida: "
         f"{j['dif_precisao_lados']}.", "",
         "| recorte | n | VP | FP | FN | VN | precisão [IC95] | recall [IC95] |",
         "|---|---|---|---|---|---|---|---|"]
    for nome, m in comp.items():
        L += [linha(f"{nome} · todos", m["geral"])]
        L += [linha(f"{nome} · {lado}", m["por_lado"][lado]) for lado in C.LADOS]
    L += ["", "| juiz | diferença de precisão entre os lados | no critério proposto |",
          "|---|---|---|"]
    L += [f"| {nome} | {m['julgamento']['dif_precisao_lados']} | "
          f"{'passaria' if m['julgamento']['vale'] else 'reprovaria: ' + '; '.join(m['julgamento']['motivos'])} |"
          for nome, m in comp.items()]
    if cal.get("escolha"):
        e = cal["escolha"]
        L += ["", f"**Escolha pré-registrada (REGISTRO.md): congelar a {e['congelar']}** — "
              f"{e['motivo']}" + (f"; recall no pior lado: {e['recall_pior_lado']}"
                                  if "recall_pior_lado" in e else "") + "."]
    der = ", ".join(f"{d['par']} ({d['motivo']})" for d in cal["derrubados_pelo_codigo"])
    L += ["", f"**Derrubados pelo código** (o modelo disse que apoia, mas disse que é "
          f"ambíguo, ou o trecho é nulo, tem menos de {MIN_PALAVRAS_TRECHO} palavras ou "
          f"não está na review): {der or 'nenhum'}.", "",
          "## Pares duvidosos", "",
          "| par | lado | dono | " + " | ".join(comp) + " | motivo do não |",
          "|---|---|---|" + "---|" * len(comp) + "---|"]
    for x in cal["pares"]:
        if x["duvidoso"]:
            vs = [sn(x["juiz_v1"])] + [sn(x["juiz_anteriores"][vv]) for vv in comp
                                       if vv not in ("v1", cal["versao"])] + [sn(x["juiz"])]
            L.append(f"| {x['par']} | {x['lado']} | {sn(x['dono'])} | " + " | ".join(vs)
                     + f" | {x['motivo'] or '—'} |")
    L += ["", f"## Erros da {cal['versao']}", ""]
    for x in cal["pares"]:
        if x["dono"] == x["juiz"]:
            continue
        amb = "" if x["ambiguo"] is None else f", {'ambíguo' if x['ambiguo'] else 'não ambíguo'}"
        if x.get("evidencia_clara") is not None:
            amb += (", evidência clara" if x["evidencia_clara"]
                    else ", sem evidência clara afirmada")
        L.append(f"### {x['par']}{' (duvidoso)' if x['duvidoso'] else ''} — {x['lado']}, "
                 f"{x['slug']}/{x['bucket']}")
        L += ["", f"- tema: \"{x['tema']}\"",
              f"- dono {sn(x['dono'])} · {cal['versao']} {sn(x['juiz'])} "
              f"(modelo disse {'apoia' if x['apoia_modelo'] else 'não apoia'}{amb}; trecho "
              f"{'encontrado' if x['trecho_encontrado'] else 'não encontrado'}, "
              f"{x['trecho_palavras']} palavras; motivo: {x['motivo'] or '—'}) · "
              + " · ".join(f"{vv} {sn(b)}" for vv, b in x["juiz_anteriores"].items())
              + ("" if not x["juiz_anteriores"] else " · ") + f"v1 {sn(x['juiz_v1'])}",
              f"- trecho: {json.dumps(x['trecho'], ensure_ascii=False)}",
              f"- raciocínio: {json.dumps((x['pensamento'] or '')[:600], ensure_ascii=False)}",
              ""]
    if not cal["erros"]:
        L.append("_(nenhum)_")
    return "\n".join(L) + "\n"


# ===========================================================================
# Estimativa de tempo (a partir do gate do gpt-oss:20b)
# ===========================================================================

MEDICAO_DIR = RAIZ / "resultado" / "auditoria-acuracia" / "local" / "gpt-oss-20b"


def estimar_tempo(pares: list[dict], regs_gate: list[dict]) -> dict:
    """Leitura do que é novo no prompt (o system fica no KV) e geração de
    tantos tokens quanto o gate gerou (mediana e p95: o raciocínio domina),
    mais a sobra por chamada. Estimativa a partir de outro prompt."""
    vel = C.medir_velocidade(regs_gate)
    ev = sorted(r["eval_count"] for r in regs_gate if r.get("ok") and r.get("eval_count"))
    tok = {"mediana": statistics.median(ev), "p95": ev[int(0.95 * (len(ev) - 1))]}
    fora = {"vel": vel, "tokens_saida": tok, "n_chamadas": len(pares)}
    for nome, t in tok.items():
        s = sum(len(user(p)) * vel["leitura_s_por_char"] + t * vel["geracao_s_por_token"]
                + vel["sobra_s_mediana"] for p in pares) + 60
        fora[f"min_{nome}"] = round(s / 60, 1)
    return fora


def md_preparo(cfg: dict, sha: str, est_ctx: dict, t_cal: dict, t_todos: dict) -> str:
    return "\n".join([
        f"# Juiz v2 — versão {cfg['versao']}", "",
        f"`config_sha256`: `{sha}`", "",
        f"- modelo `{MODELO}`, think `{THINK}`, seed {SEED}, temperatura do modelo",
        f"- num_predict {NUM_PREDICT}, num_ctx **{cfg['num_ctx']}**", "",
        "## Contexto", "",
        f"Maior par dos {t_todos['n_chamadas']}: `{est_ctx['maior_id_par']}` — review de "
        f"{est_ctx['maior_chars_review']} caracteres, prompt inteiro de "
        f"{est_ctx['maior_chars_prompt']}.", "",
        f"Cota conservadora: {RAZAO_TOKENS_POR_CHAR} token/caractere (no gate do gpt-oss "
        f"o máximo foi 0,343 em 417 prompts) → ≤ {est_ctx['cota_tokens_prompt']} tokens "
        f"de prompt + {NUM_PREDICT} de saída = {est_ctx['precisa']} → menor múltiplo de 512: "
        f"**{est_ctx['menor_multiplo_512']}**. É cota, não medição: `medir-contexto` "
        f"conta os {MEDICAO_N_PARES} maiores prompts no servidor antes de o juiz rodar.", "",
        "## Tempo (estimativa, não medição)", "",
        "Das velocidades do gate do gpt-oss:20b neste notebook; a saída é a do gate "
        f"(mediana {t_cal['tokens_saida']['mediana']:.0f} tokens, p95 "
        f"{t_cal['tokens_saida']['p95']} — o raciocínio domina).", "",
        "| execução | chamadas | mediana | p95 |", "|---|---|---|---|",
        f"| calibração (40 pares) | {t_cal['n_chamadas']} | ~{t_cal['min_mediana']:.0f} min | "
        f"~{t_cal['min_p95']:.0f} min |",
        f"| todos (900 pares, só com a versão congelada) | {t_todos['n_chamadas']} | "
        f"~{t_todos['min_mediana']:.0f} min | ~{t_todos['min_p95']:.0f} min |", "",
        f"`medir-contexto`: {MEDICAO_N_PARES} chamadas com num_ctx {MEDICAO_NUM_CTX} e 1 token "
        "de saída, mais a recarga do modelo ao trocar de janela — poucos minutos.", ""])


# ===========================================================================
# Subcomandos
# ===========================================================================

def _exigir_ambiente() -> None:
    if os.environ.get(VAR_TEMPERATURA):
        raise SystemExit(f"{VAR_TEMPERATURA} está definida — o juiz v2 usa a temperatura "
                         f"do modelo, parte da configuração. Remova a variável.")


def _chamador(*, num_ctx: int, num_predict: int, schema: dict):
    from espectro24 import local_ollama

    def chamar(sys_txt: str, user_txt: str) -> dict:
        return local_ollama.resposta_json_local(
            sys_txt, user_txt, estagio=ESTAGIO, modelo=MODELO, schema=schema,
            num_predict=num_predict, num_ctx=num_ctx, think=THINK, seed=SEED)
    return chamar


def _exigir_modelo() -> None:
    from gerar_prosa_local import _exigir_modelo as exigir

    exigir(MODELO)


def arq_contexto(versao: str) -> Path:
    return DIR_V2 / f"contexto_medido_{versao}.json"


def cmd_preparar(a) -> None:
    if len(VERSOES) > MAX_VERSOES:
        raise SystemExit(f"{len(VERSOES)} versões — o limite é {MAX_VERSOES} (2 ajustes)")
    pares = C._ler_jsonl(a.dir / C.ARQ_ENTRADA)
    cal = pares_calibracao(a.dir)
    cfg, sha = config(), config_sha256()
    est = estimar_contexto(pares)
    if not est["cabe"]:
        raise SystemExit(f"a cota de contexto ({est['precisa']}) não cabe em num_ctx={num_ctx()}")
    regs = [r for n in (1, 2, 3)
            for r in C._ler_jsonl(a.medicao_dir / f"classificacao_passe_{n}.jsonl")]
    if not regs:
        raise SystemExit(f"sem os registros do gate do gpt-oss em {a.medicao_dir} "
                         f"(estão no branch gate-local)")
    t_cal, t_todos = estimar_tempo(cal, regs), estimar_tempo(pares, regs)
    C._json(a.dir / DIR_V2 / f"config_{VERSAO_ATUAL}.json",
            {"config_sha256": sha, **cfg, "contexto_estimado": est})
    C._escrever(a.dir / DIR_V2 / f"preparo_{VERSAO_ATUAL}.md",
                md_preparo(cfg, sha, est, t_cal, t_todos))
    print(f"{VERSAO_ATUAL} · config {sha[:16]}… · contexto: cota {est['precisa']} → "
          f"num_ctx {num_ctx()} · calibração ~{t_cal['min_mediana']:.0f} min "
          f"(p95 {t_cal['min_p95']:.0f})")


def cmd_medir_contexto(a) -> None:
    _exigir_ambiente()
    pares = C._ler_jsonl(a.dir / C.ARQ_ENTRADA)
    if not pares:
        raise SystemExit(f"{a.dir / C.ARQ_ENTRADA} não encontrado ou vazio")
    _exigir_modelo()
    chamar = _chamador(num_ctx=MEDICAO_NUM_CTX, num_predict=1, schema=schema())
    medidos = []
    for p in maiores_pares(pares):
        resp = chamar(system(), user(p))
        if resp.get("think") != THINK:
            raise SystemExit(f"o servidor recusou think={THINK} ({resp.get('think')!r})")
        medidos.append({"id_par": p["id_par"], "chars_prompt": chars_do_prompt(p),
                        "chars_review": len(p["texto"]),
                        "prompt_eval_count": resp["prompt_eval_count"],
                        "modelo_efetivo": resp.get("modelo_efetivo")})
        print(f"  {p['id_par']}: {medidos[-1]['chars_prompt']} chars → "
              f"{resp['prompt_eval_count']} tokens", flush=True)
    jul = julgar_medicao(medidos)
    C._json(a.dir / arq_contexto(VERSAO_ATUAL),
            {"versao": VERSAO_ATUAL, "config_sha256": config_sha256(),
             "medicao_num_ctx": MEDICAO_NUM_CTX, "medidos": medidos, **jul,
             "ts": datetime.now(timezone.utc).isoformat(timespec="seconds")})
    print(("CABE" if jul["cabe"] else "NÃO CABE") +
          f": maior prompt {jul['max_prompt_tokens']} + {NUM_PREDICT} = {jul['precisa']} "
          f"em num_ctx {num_ctx()} (folga {jul['folga']})")
    if not jul["cabe"]:
        raise SystemExit(1)


def cmd_juiz(a) -> None:
    _exigir_ambiente()
    versao = VERSAO_ATUAL
    med = a.dir / arq_contexto(versao)
    if not med.exists():
        raise SystemExit(f"sem {med} — rode `medir-contexto` antes")
    m = C._ler_json(med)
    if m.get("config_sha256") != config_sha256(versao) or not m.get("cabe"):
        raise SystemExit(f"{med} é de outra configuração ou não cabe — rode `medir-contexto`")
    if a.calibracao:
        pares, saida = pares_calibracao(a.dir), a.dir / DIR_V2 / f"calibracao_{versao}_saida.jsonl"
    else:
        if CONGELADA != versao:
            raise SystemExit(f"os 900 pares só rodam com a versão CONGELADA (hoje: "
                             f"{CONGELADA!r}); congele e registre o hash antes")
        pares, saida = C._ler_jsonl(a.dir / C.ARQ_ENTRADA), a.dir / DIR_V2 / f"saida_{versao}.jsonl"
    _exigir_modelo()
    print(f"{len(pares)} pares · {MODELO} think={THINK} · num_ctx {num_ctx(versao)} · "
          f"versão {versao} ({config_sha256(versao)[:16]}…)", flush=True)
    r = rodar(pares, saida, _chamador(num_ctx=num_ctx(versao), num_predict=NUM_PREDICT,
                                     schema=schema(versao)), versao=versao)
    ok = {x["id_par"] for x in C._ler_jsonl(saida)
          if x.get("ok") and x.get("config_sha256") == config_sha256(versao)}
    faltam = sum(1 for p in pares if p["id_par"] not in ok)
    print(f"\n{r['rodados']} chamadas em {r['parede_s'] / 60:.0f} min · falhas {r['falhas']} · "
          f"pares sem veredito: {faltam}" + (" — rode de novo" if faltam else " — completo"))


def cmd_calibrar(a) -> None:
    versao = a.versao or VERSAO_ATUAL
    cal = calibracao(a.dir, versao)
    C._json(a.dir / DIR_V2 / f"calibracao_{versao}.json", cal)
    C._escrever(a.dir / DIR_V2 / f"calibracao_{versao}.md", md_calibracao(cal))
    g, j = cal["geral"], cal["julgamento"]
    print(f"CALIBRAÇÃO {versao} (não é validação) · P={g['precisao']} R={g['recall']} · "
          f"dif. lados {j['dif_precisao_lados']} · " +
          ("passaria" if j["vale"] else "reprovaria: " + "; ".join(j["motivos"])) +
          (f" · escolha pré-registrada: congelar a {cal['escolha']['congelar']}"
           if cal.get("escolha") else ""))


# ===========================================================================
# Validação — os 40 pares NOVOS, só com a versão congelada
# ===========================================================================

# Outra semente que a do rótulo antigo: o sorteio novo não repete o antigo.
SEMENTE_VALIDACAO = 20261020
# A amostra nova fica longe do mapa (o mapa diz o lado; o documento, não).
ARQ_DOC_VALIDACAO = Path("rotulagem_validacao") / "rotulagem_dono.md"
ARQ_ROTULOS_VALIDACAO = Path("rotulagem_validacao") / "rotulos_dono.csv"
ARQ_MAPA_VALIDACAO = Path("mapa") / "validacao_mapa.json"


def exigir_congelada() -> str:
    if CONGELADA is None or CONGELADA not in VERSOES:
        raise SystemExit("nenhuma versão CONGELADA — a amostra nova e a validação só "
                         "existem depois do congelamento")
    return CONGELADA


def sortear_validacao(pares: list[dict], excluir: set[str]) -> list[dict]:
    """Os 40 novos: o mesmo sorteio da rotulagem antiga (`C.sortear_rotulo`:
    20 por lado, cotas iguais por filme — 4 —, metade dos ranks 1-2 e metade
    dos 3-5, no máximo um par por bullet), com outra semente e SEM nenhum
    dos pares da calibração."""
    restantes = [p for p in pares if p["id_par"] not in excluir]
    amostra = C.sortear_rotulo(restantes, semente=SEMENTE_VALIDACAO)
    assert not {p["id_par"] for p in amostra} & excluir
    return amostra


def montar_doc_validacao(amostra: list[dict], titulos: dict[str, str], selo: str) -> str:
    """O documento que o dono LÊ, no formato do da rotulagem antiga. Não diz
    o lado, o modelo, a similaridade, o rank, nem a resposta do juiz. O
    critério é o guia do dono (`CRITERIO_DONO`), o mesmo da calibração."""
    L = ["# Rotulagem manual (validação) — o bullet tem apoio nesta review?", "",
         f"São {len(amostra)} pares NOVOS (nenhum da rotulagem anterior). Em cada um, "
         "um TEMA (o bullet da síntese, com a descrição que aparece em \"Aprofundar\") "
         "e UMA review do mesmo grupo.", "",
         "> **Esta review sustenta o bullet?**", "",
         CRITERIO_DONO, "",
         f"Responda em `{ARQ_ROTULOS_VALIDACAO.name}` (mesma pasta), uma linha por par: "
         "`sim` ou `não`. Não deixe em branco — par sem rótulo trava a validação.", ""]
    for k, p in enumerate(amostra, 1):
        L += ["---", "", f"## P{k:02d} — {titulos[p['slug']]} · {C.GRUPO[p['bucket']]}", "",
              f"**Tema:** {p['tema']}", "", f"**Descrição:** {p['exemplo']}", "",
              f"**Review** (nota {p['nivel']} de 5 estrelas):", ""]
        L += ["> " + linha if linha.strip() else ">" for linha in p["texto"].splitlines()]
        L += ["", f"**P{k:02d} — a review sustenta o bullet?** sim / não", ""]
    L += ["---", "", f"_Selo do mapeamento (sha256): `{selo}`_", ""]
    return "\n".join(L)


def _titulos(d: Path) -> dict[str, str]:
    eixo = C._ler_json(d / C.ARQ_EIXO)
    return {s: (C._ler_json(C.RESULTADO_DIR / f"{s}.json").get("ficha") or {}).get("titulo")
            or s for s in eixo["meta"]["filmes"]}


def mapa_validacao_conferido(d: Path) -> dict:
    mapa = C._ler_json(d / ARQ_MAPA_VALIDACAO)
    selo = C._sha256_texto(json.dumps({k: mapa[k] for k in ("semente", "pares")},
                                      sort_keys=True, ensure_ascii=False))
    if selo != mapa["sha256"]:
        raise SystemExit("o mapeamento da validação não confere com o próprio selo")
    antigos = set(mapa_conferido(d)["pares"].values())
    if set(mapa["pares"].values()) & antigos:
        raise SystemExit("a amostra de validação repete pares da calibração")
    return mapa


def cmd_amostra_validacao(a) -> None:
    versao = exigir_congelada()
    csv_ = a.dir / ARQ_ROTULOS_VALIDACAO
    if csv_.exists():
        with csv_.open(encoding="utf-8", newline="") as fh:
            preenchidos = [l for l in csv.DictReader(fh) if (l.get("rotulo") or "").strip()]
        if preenchidos:
            raise SystemExit(f"{csv_} já tem {len(preenchidos)} rótulos — o sorteio nunca "
                             f"é refeito por cima do rótulo do dono")
        raise SystemExit(f"{csv_} já existe — a amostra nova é sorteada uma vez só")
    pares = C._ler_jsonl(a.dir / C.ARQ_ENTRADA)
    antigos = set(mapa_conferido(a.dir)["pares"].values())
    amostra = sortear_validacao(pares, antigos)
    mapa = {"semente": SEMENTE_VALIDACAO,
            "pares": {f"P{k:02d}": p["id_par"] for k, p in enumerate(amostra, 1)}}
    selo = C._sha256_texto(json.dumps(mapa, sort_keys=True, ensure_ascii=False))
    C._json(a.dir / ARQ_MAPA_VALIDACAO,
            {**mapa, "sha256": selo, "congelada": versao,
             "config_sha256": config_sha256(versao),
             "excluidos": "os 40 pares de mapa/rotulagem_mapa.json (calibração)"})
    C._escrever(a.dir / ARQ_DOC_VALIDACAO, montar_doc_validacao(amostra, _titulos(a.dir), selo))
    C._escrever(csv_, "par,rotulo\n" + "".join(f"P{k:02d},\n"
                                                 for k in range(1, len(amostra) + 1)))
    print(f"{len(amostra)} pares novos → {a.dir / ARQ_DOC_VALIDACAO} · selo {selo[:16]}…")


def validacao(d: Path) -> dict:
    """A versão congelada contra o rótulo NOVO do dono, só nos 40 novos, com
    o critério pré-registrado (`CRITERIO_V2`, sem mudança)."""
    versao = exigir_congelada()
    mapa = mapa_validacao_conferido(d)
    ids = set(mapa["pares"].values())
    entrada = {p["id_par"]: p for p in C._ler_jsonl(d / C.ARQ_ENTRADA)}
    pares = [entrada[i] for i in mapa["pares"].values()]
    regs = [r for r in C._ler_jsonl(d / DIR_V2 / f"saida_{versao}.jsonl") if r["id_par"] in ids]
    ver = vereditos(pares, regs, versao)
    dono = C.ler_rotulos(d / ARQ_ROTULOS_VALIDACAO, list(mapa["pares"]))
    linhas = []
    for par, id_par in mapa["pares"].items():
        p, v = entrada[id_par], ver[id_par]
        linhas.append({"par": par, "id_par": id_par, "lado": p["lado"], "slug": p["slug"],
                       "bucket": p["bucket"], "tema": p["tema"], "dono": dono[par],
                       "juiz": v["apoio"], "motivo": v["motivo"], "trecho": v["trecho"],
                       "pensamento": v["pensamento"]})
    geral = C.matriz([(x["dono"], x["juiz"]) for x in linhas])
    por_lado = {lado: C.matriz([(x["dono"], x["juiz"]) for x in linhas if x["lado"] == lado])
                for lado in C.LADOS}
    return {"versao": versao, "config_sha256": config_sha256(versao),
            "selo_mapa": mapa["sha256"], "geral": geral, "por_lado": por_lado,
            "julgamento": julgar(geral, por_lado),
            "erros": [x for x in linhas if x["dono"] != x["juiz"]], "pares": linhas}


def _aviso_nao_vale(j: dict, versao: str) -> list[str]:
    return ["> **ESTE RESULTADO NÃO VALE.** O juiz " + versao + " reprovou na validação "
            "contra o rótulo do dono nos 40 pares novos (" + "; ".join(j["motivos"]) +
            "). Os números abaixo estão aqui só para auditoria; nenhuma conclusão "
            "pode sair deles.", ""]


def md_validacao(val: dict) -> str:
    def linha(nome, m):
        return (f"| {nome} | {m['n']} | {m['vp']} | {m['fp']} | {m['fn']} | {m['vn']} | "
                f"{m['precisao']} {m['precisao_ic95']} | {m['recall']} {m['recall_ic95']} |")
    j, cr = val["julgamento"], CRITERIO_V2
    L = [] if j["vale"] else _aviso_nao_vale(j, val["versao"])
    L += [f"# Validação do juiz v2 — versão congelada {val['versao']}", "",
          f"Configuração `{val['config_sha256']}` · 40 pares NOVOS (nenhum da calibração) · "
          f"rótulo do dono · selo do mapa `{val['selo_mapa'][:16]}…`", "",
          ("**O JUIZ PASSOU** no critério pré-registrado" if j["vale"] else
           "**O JUIZ REPROVOU** no critério pré-registrado: " + "; ".join(j["motivos"]))
          + f" — precisão ≥ {cr['precisao_min']}, recall ≥ {cr['recall_min']}, diferença "
          f"de precisão entre os lados ≤ {cr['dif_precisao_lados_max']} (medida: "
          f"{j['dif_precisao_lados']}).", "",
          "| recorte | n | VP | FP | FN | VN | precisão [IC95] | recall [IC95] |",
          "|---|---|---|---|---|---|---|---|", linha("todos", val["geral"])]
    L += [linha(lado, val["por_lado"][lado]) for lado in C.LADOS]
    L += ["", "## Erros", ""]
    for x in val["erros"]:
        L += [f"### {x['par']} — {x['lado']}, {x['slug']}/{x['bucket']}", "",
              f"- tema: \"{x['tema']}\"",
              f"- dono {'sim' if x['dono'] else 'não'} · juiz {'sim' if x['juiz'] else 'não'} "
              f"(motivo: {x['motivo'] or '—'})",
              f"- trecho: {json.dumps(x['trecho'], ensure_ascii=False)}",
              f"- raciocínio: {json.dumps((x['pensamento'] or '')[:600], ensure_ascii=False)}",
              ""]
    if not val["erros"]:
        L.append("_(nenhum)_")
    return "\n".join(L) + "\n"


def cmd_validar(a) -> None:
    val = validacao(a.dir)
    v = val["versao"]
    C._json(a.dir / DIR_V2 / f"validacao_{v}.json", val)
    C._escrever(a.dir / DIR_V2 / f"validacao_{v}.md", md_validacao(val))
    g, j = val["geral"], val["julgamento"]
    print(("JUIZ VALE" if j["vale"] else "JUIZ NÃO VALE: " + "; ".join(j["motivos"])) +
          f" · {v} · P={g['precisao']} R={g['recall']} · dif. lados {j['dif_precisao_lados']}")


def md_fidelidade(apoios: list[dict], val: dict, titulos: dict[str, str]) -> str:
    """O relatório de fidelidade dos bullets com o juiz congelado. O corpo é o
    de `C.md_final` (mesmas tabelas da Parte 2); o cabeçalho é o da validação
    nos 40 pares novos e, se ela reprovou, o aviso vem na PRIMEIRA linha."""
    j, g = val["julgamento"], val["geral"]
    L = [] if j["vale"] else _aviso_nao_vale(j, val["versao"])
    L += [f"# Fidelidade dos bullets — juiz {val['versao']} (congelado)", "",
          f"Configuração `{val['config_sha256']}`. Validação nos 40 pares novos: "
          f"precisão {g['precisao']} {g['precisao_ic95']}, recall {g['recall']} "
          f"{g['recall_ic95']}; por lado: " + "; ".join(
              f"{lado} P {val['por_lado'][lado]['precisao']} / R "
              f"{val['por_lado'][lado]['recall']}" for lado in C.LADOS) +
          f" — {'passou' if j['vale'] else 'REPROVOU'} no critério pré-registrado.", ""]
    corpo = C.md_final(apoios, {**val, "julgamento": {**j, "vale": True}}, titulos).splitlines()
    ini = next(k for k, l in enumerate(corpo) if l.startswith("Apoio = "))
    velho = 'Apoio = o juiz disse "menciona" para a review.'
    assert corpo[ini].startswith(velho), corpo[ini]
    corpo[ini] = (f"Apoio = o juiz {val['versao']} deu apoio à review (ideia principal do "
                  "título, evidência clara e frase de prova achada nela)."
                  + corpo[ini][len(velho):])
    return "\n".join(L + corpo[ini:]) + "\n"


def cmd_relatorio(a) -> None:
    versao = exigir_congelada()
    arq_val = a.dir / DIR_V2 / f"validacao_{versao}.json"
    if not arq_val.exists():
        raise SystemExit(f"sem {arq_val}: o relatório não sai antes de o juiz ser validado "
                         f"nos 40 pares novos (`validar`)")
    val = C._ler_json(arq_val)
    if val.get("config_sha256") != config_sha256(versao):
        raise SystemExit(f"{arq_val} é de outra configuração — rode `validar` de novo")
    entrada = C._ler_jsonl(a.dir / C.ARQ_ENTRADA)
    ver = {k: v["apoio"] for k, v in vereditos(
        entrada, C._ler_jsonl(a.dir / DIR_V2 / f"saida_{versao}.jsonl"), versao).items()}
    eixo = C._ler_json(a.dir / C.ARQ_EIXO)
    apoios = C.apoio_por_bullet(eixo["bullets"], entrada, ver)
    final = {"vale": val["julgamento"]["vale"], "versao": versao,
             "config_sha256": val["config_sha256"], "validacao": val["geral"],
             "validacao_por_lado": val["por_lado"],
             "por_lado": {lado: C.resumo([x for x in apoios if x["lado"] == lado])
                          for lado in C.LADOS},
             "por_filme": {s: {lado: C.resumo([x for x in apoios if x["lado"] == lado
                                               and x["slug"] == s]) for lado in C.LADOS}
                           for s in eixo["meta"]["filmes"]},
             "cruzamento_parte1": {lado: C.cruzamento([x for x in apoios if x["lado"] == lado])
                                   for lado in C.LADOS},
             "bullets": apoios}
    C._json(a.dir / DIR_V2 / f"fidelidade_{versao}.json", final)
    C._escrever(a.dir / DIR_V2 / f"fidelidade_{versao}.md",
                md_fidelidade(apoios, val, _titulos(a.dir)))
    print(("" if final["vale"] else "NÃO VALE (juiz reprovado) · ") +
          " · ".join(f"{lado}: ≥1 {final['por_lado'][lado]['frac_ge1']:.0%}, "
                     f"≥2 {final['por_lado'][lado]['frac_ge2']:.0%}" for lado in C.LADOS))


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawTextHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for nome, func in (("preparar", cmd_preparar), ("medir-contexto", cmd_medir_contexto),
                       ("juiz", cmd_juiz), ("calibrar", cmd_calibrar),
                       ("amostra-validacao", cmd_amostra_validacao),
                       ("validar", cmd_validar), ("relatorio", cmd_relatorio)):
        p = sub.add_parser(nome)
        p.set_defaults(func=func)
        p.add_argument("--dir", type=Path, required=True,
                       help="pasta da checagem (NUNCA dentro de resultado/)")
        if nome == "preparar":
            p.add_argument("--medicao-dir", type=Path, default=MEDICAO_DIR,
                           help="registros do gate do gpt-oss:20b (velocidade medida)")
        if nome == "juiz":
            g = p.add_mutually_exclusive_group(required=True)
            g.add_argument("--calibracao", action="store_true",
                           help="só os 40 pares do rótulo antigo")
            g.add_argument("--todos", action="store_true",
                           help="os 900 pares (só com a versão congelada)")
        if nome == "calibrar":
            p.add_argument("--versao", help=f"padrão: {VERSAO_ATUAL}")
    a = ap.parse_args(argv)
    C.exigir_fora_de_resultado(a.dir)
    a.func(a)


if __name__ == "__main__":
    main()
