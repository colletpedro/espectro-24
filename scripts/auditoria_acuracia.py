"""Auditoria de acurácia da classificação de 10 eixos (`TAXONOMIA_10.md`).

**O que este script NÃO faz:** não reclassifica o corpus, não muda taxonomia
nem prompt, não calcula acurácia nenhuma até que o humano devolva as
anotações. Ele prepara o instrumento (Entrega 1), prepara o script de cálculo
(Entrega 2, não executado aqui) e mede estabilidade entre execuções (Entrega
3, que é medição independente do julgamento humano).

**v2 (sessão de 2026-08-10): fonte trocada de passada única para o CONSENSO
de votação (3 passadas, eixo entra se ≥2/3 — ver `votacao-3/consenso.jsonl`).
A amostra v1 (`_arquivo_v1_passada-unica/`) foi amostrada sobre
`classificacoes.jsonl` e está arquivada — os estratos de n_eixos mudaram sob
consenso, então anotar contra ela mediria a acurácia de uma classificação que
não é mais a de produção.**

A votação mediu que o modelo concorda CONSIGO MESMO (65,0% de reprodutibilidade
entre consenso(1,2,3) e consenso(2,3,4)) — não mediu se ele está CERTO. A
única auditoria humana que este projeto já fez de um classificador
(experimento Ollama, `VALIDACAO_DEEPSEEK.md`) achou precisão de 96% com
RECALL ruim — problema que a distribuição agregada não revela. Esta é a
mesma pergunta, sobre o classificador consensual de produção.

Uso:
    python scripts/auditoria_acuracia.py amostra        # Entrega 1
    python scripts/auditoria_acuracia.py estabilidade   # Entrega 3 (chamadas LLM, centavos)
    python scripts/auditoria_acuracia.py metricas        # Entrega 2 — só depois das anotações

Saídas em `resultado/auditoria-acuracia/`.
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Lock

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

from classificar_10 import (  # noqa: E402  — MESMO prompt/eixos que produziram o corpus
    EIXOS,
    MODELO,
    SYSTEM,
    _normalizar,
    recuperar_eixo,
    taxonomia_id,
)
from espectro24.synthesize import (  # noqa: E402
    deepseek_client,
    deepseek_resposta,
    deepseek_uso,
)

FONTE_AMOSTRA = RAIZ / "resultado" / "votacao-3" / "amostra.json"
FONTE_CONSENSO = RAIZ / "resultado" / "votacao-3" / "consenso.jsonl"

SAIDA = RAIZ / "resultado" / "auditoria-acuracia"
ARQ_INDICE = SAIDA / "amostra.json"
ARQ_LEITURA = SAIDA / "leitura.md"
ARQ_GABARITO = SAIDA / "gabarito_modelo.json"
ARQ_ESTABILIDADE_BRUTO = SAIDA / "estabilidade_bruto.jsonl"
ARQ_ESTABILIDADE_RELATORIO = SAIDA / "estabilidade_relatorio.json"
ARQ_METRICAS = SAIDA / "metricas_relatorio.json"

# Semente fixa e registrada (v1.9.6/sessão seguinte) — mesma convenção de
# `classificar_10.SEMENTE`: data de autoria, não escolhida para favorecer
# nenhum resultado.
SEMENTE = 20260810
N_AMOSTRA = 100
N_ESTABILIDADE = 200

BUCKETS = ("negativas", "medianas", "positivas")
PERFIS = ("aclamado", "arthouse", "divisivo", "invertido", "obscuro")

FRONTEIRAS_N_CHARS_PISO = 200  # MIN_CHARS=150 + folga de leitura — "perto do piso"


# ===========================================================================
# Carga e junção — bruto (texto) + CONSENSO (eixos de ≥2/3 passadas), pelo id
# ===========================================================================

def _carregar_universo() -> list[dict]:
    """Junta `votacao-3/amostra.json` (texto) com `votacao-3/consenso.jsonl`
    (eixos consensuais + votos) por `(slug, bucket, id)`. `consenso.jsonl` já
    carrega o conjunto consensual reparado (sem nomes malformados — a
    votação já filtrou isso); nenhum `recuperar_eixo` extra é necessário
    aqui. `votos` é preservado por review (ex.: `{"ritmo": 3, "livre": 2}`)
    — é o que permite a quebra 3/3-vs-2/3 da Entrega 3.
    """
    amostra = json.loads(FONTE_AMOSTRA.read_text(encoding="utf-8"))
    texto_por_chave = {(r["slug"], r["bucket"], r["id"]): r["texto"]
                       for r in amostra["reviews"]}

    vistos: set[tuple] = set()
    universo: list[dict] = []
    for linha in FONTE_CONSENSO.read_text(encoding="utf-8").splitlines():
        if not linha.strip():
            continue
        r = json.loads(linha)
        chave = (r["slug"], r["bucket"], r["id"])
        if chave in vistos:
            continue
        vistos.add(chave)

        texto = texto_por_chave.get(chave)
        if texto is None:
            continue
        r = dict(r, texto=texto)
        universo.append(r)
    return universo


def _votos_minimos(r: dict) -> dict[str, int]:
    """Votos (3 ou 2) de cada eixo que ENTROU no conjunto consensual —
    filtra `votos` (que também guarda contagens de eixos que NÃO entraram,
    ex. voto 1/3) para os eixos de fato atribuídos."""
    return {e: r["votos"].get(e, 0) for e in r["eixos"]}


def _classe_confianca(r: dict) -> str:
    """[Entrega 1/2] `unanime` se TODO eixo consensual saiu 3/3; `maioria`
    se ao menos um saiu 2/3; `vazio` se nenhum eixo (nem `livre`) alcançou
    consenso — 0,68% do corpus, categoria que só existe sob votação."""
    if not r["eixos"]:
        return "vazio"
    votos = _votos_minimos(r)
    return "unanime" if all(v == 3 for v in votos.values()) else "maioria"


def _grupo_n_eixos(r: dict) -> str:
    """[Entrega 1] Agrupamento de `número de eixos atribuídos`, EXCLUINDO
    `livre` da contagem — a mesma convenção do histograma de
    `TAXONOMIA_10.md` §Entrega 2. As duas caudas (`0` e `7+`) são as que a
    auditoria deliberadamente sobre-amostra."""
    n = len([e for e in r["eixos"] if e != "livre"])
    if n == 0:
        return "0"
    if n <= 2:
        return "1-2"
    if n <= 4:
        return "3-4"
    if n <= 6:
        return "5-6"
    return "7+"


# ===========================================================================
# Entrega 1 — amostra estratificada
# ===========================================================================

def _tira(pool: list[dict], k: int, rng: random.Random) -> list[dict]:
    """Sorteia até `k` itens de `pool` (sem repor) e os REMOVE do pool
    original — dedupe entre estratos é assim que a amostra nunca conta a
    mesma review duas vezes sob rótulos diferentes."""
    k = min(k, len(pool))
    escolhidas = rng.sample(pool, k)
    ids = {id(x) for x in escolhidas}
    pool[:] = [x for x in pool if id(x) not in ids]
    return escolhidas


def montar_amostra_auditoria(universo: list[dict], rng: random.Random
                             ) -> tuple[list[dict], dict]:
    """[Entrega 1] Aloca 100 reviews por estrato, deliberadamente NÃO
    proporcional — as duas caudas de `n_eixos`, o perfil `obscuro` e as
    duas quebras NOVAS de confiança (`maioria` 2/3, `unanime` 3/3,
    `vazio`) são sobre-amostradas de propósito.

    Alocação (soma 100), com o racional de cada bloco:

    - **4 — `consenso_vazio`** (não repartido por bucket — o grupo inteiro
      tem só 27/3990 = 0,68% do corpus; exigir 4 já é ~15% dele). Nenhum
      eixo, nem `livre`, alcançou maioria — categoria que só existe sob
      votação, ninguém olhou ainda.
    - **24 — `n_eixos=0`** (8 por bucket, excluindo o que já saiu em
      `consenso_vazio`). É a cauda de RECALL: review com zero eixos pode
      ser corretamente livre, ou pode ser o modelo perdendo sinal.
    - **24 — `n_eixos>=7`** (8 por bucket). É a cauda de GENEROSIDADE:
      risco de o modelo atribuir eixo demais.
    - **12 — comprimento perto do piso** (`n_chars<=200`, 4 por bucket,
      excluindo o que já saiu acima). É onde o experimento Ollama achou o
      defeito de recall — review curta dá menos texto para o modelo errar
      por falta de sinal, ou generalizar demais a partir de pouco.
    - **6 — perfil `obscuro`** (2 por bucket, quando disponível). Só
      `obsession-2026` qualifica — sem alocação própria, esse perfil não
      apareceria quase nunca por sorteio puro.
    - **10 — `confianca=maioria`** e **10 — `confianca=unanime`** (não
      repartidos por bucket — a dimensão de interesse aqui é a confiança do
      voto, não o bucket). É a quebra mais informativa desta rodada: se
      unânime for acurado e maioria for duvidoso, isso vira régua de
      confiança para o schema.
    - **10 — resto**, round-robin por (bucket × perfil ≠ obscuro), cobrindo
      os grupos de `n_eixos` médios (1-2, 3-4, 5-6) que as caudas acima não
      tocam.

    Onde um estrato não tem material suficiente, o déficit fica registrado
    (não redistribuído silenciosamente) — mesma política de honestidade do
    resto do projeto: um estrato curto é dado a conhecer, não escondido
    enchendo com outro estrato sem aviso.
    """
    pool = list(universo)
    por_bucket = defaultdict(list)
    for r in pool:
        por_bucket[r["bucket"]].append(r)

    escolhidas: list[dict] = []
    deficits: dict[str, int] = {}

    def bloco(nome: str, filtro, alvo_por_bucket: int):
        for b in BUCKETS:
            sub = [r for r in por_bucket[b] if filtro(r)]
            tiradas = _tira(sub, alvo_por_bucket, rng)
            for r in tiradas:
                pool.remove(r)
                por_bucket[b].remove(r)
                escolhidas.append(dict(r, estrato=nome))
            falta = alvo_por_bucket - len(tiradas)
            if falta > 0:
                deficits[f"{nome}/{b}"] = falta

    def bloco_flat(nome: str, filtro, alvo_total: int):
        """Como `bloco`, mas sem repartição por bucket — para estratos cuja
        dimensão de interesse não é o bucket (confiança do voto, consenso
        vazio)."""
        sub = [r for r in pool if filtro(r)]
        tiradas = _tira(sub, alvo_total, rng)
        for r in tiradas:
            pool.remove(r)
            por_bucket[r["bucket"]].remove(r)
            escolhidas.append(dict(r, estrato=nome))
        falta = alvo_total - len(tiradas)
        if falta > 0:
            deficits[nome] = falta

    bloco_flat("consenso_vazio", lambda r: _classe_confianca(r) == "vazio", 4)
    bloco("n_eixos=0", lambda r: _grupo_n_eixos(r) == "0", 8)
    bloco("n_eixos>=7", lambda r: _grupo_n_eixos(r) == "7+", 8)
    bloco("comprimento<=200", lambda r: r["n_chars"] <= FRONTEIRAS_N_CHARS_PISO, 4)
    bloco("perfil=obscuro", lambda r: r["perfil"] == "obscuro", 2)
    bloco_flat("confianca=maioria", lambda r: _classe_confianca(r) == "maioria", 10)
    bloco_flat("confianca=unanime", lambda r: _classe_confianca(r) == "unanime", 10)

    # Resto: round-robin (bucket × perfil não-obscuro), cobrindo n_eixos médio.
    restante = N_AMOSTRA - len(escolhidas)
    celulas = [(b, p) for b in BUCKETS for p in PERFIS if p != "obscuro"]
    rng.shuffle(celulas)
    i = 0
    tentativas_sem_sucesso = 0
    while restante > 0 and tentativas_sem_sucesso < len(celulas):
        b, p = celulas[i % len(celulas)]
        i += 1
        sub = [r for r in por_bucket[b] if r["perfil"] == p]
        tirada = _tira(sub, 1, rng)
        if tirada:
            r = tirada[0]
            pool.remove(r)
            por_bucket[b].remove(r)
            escolhidas.append(dict(r, estrato="resto_round_robin"))
            restante -= 1
            tentativas_sem_sucesso = 0
        else:
            tentativas_sem_sucesso += 1
    if restante > 0:
        deficits["resto_round_robin"] = restante

    # Ordem de APRESENTAÇÃO embaralhada de novo — a ordem de alocação por
    # estrato não deve vazar para a leitura (evita que o humano perceba
    # blocos e desenvolva expectativa por posição).
    rng.shuffle(escolhidas)

    telemetria = {
        "n_alvo": N_AMOSTRA, "n_obtido": len(escolhidas),
        "deficits_por_estrato": deficits,
        "composicao_por_estrato": dict(Counter(r["estrato"] for r in escolhidas)),
        "composicao_por_bucket": dict(Counter(r["bucket"] for r in escolhidas)),
        "composicao_por_perfil": dict(Counter(r["perfil"] for r in escolhidas)),
        "composicao_por_n_eixos_grupo": dict(Counter(
            _grupo_n_eixos(r) for r in escolhidas)),
        "composicao_por_confianca": dict(Counter(
            _classe_confianca(r) for r in escolhidas)),
    }
    return escolhidas, telemetria


CHECKLIST_EIXOS = list(EIXOS)


def _bloco_markdown(ordem: int, r: dict) -> str:
    texto = r["texto"].strip()
    linhas_eixo = "\n".join(f"- [ ] {e}" for e in CHECKLIST_EIXOS)
    return f"""---

### #{ordem:03d} · `{r['id']}` · {r['slug']} ({r['perfil']}) · {r['bucket']} · {r['nivel']}★ · {r['n_chars']} chars

> {texto.replace(chr(10), chr(10) + '> ')}

**Meus eixos** (marque com `x` os que a review realmente menciona):

{linhas_eixo}
- [ ] livre — temas: ____________________

**Observação (opcional):** ____________________
"""


def escrever_leitura_md(escolhidas: list[dict]) -> None:
    cabecalho = f"""# Auditoria de acurácia — leitura e anotação

**Gerado:** semente {SEMENTE} · {len(escolhidas)} reviews · taxonomia
`{taxonomia_id()}` (10 eixos, ver `TAXONOMIA_10.md`) · amostrado sobre o
CONSENSO de votação de 3 passadas (`votacao-3/consenso.jsonl`), não sobre
uma classificação de passada única.

**Como anotar:** para cada review, marque `[x]` em todo eixo que VOCÊ
atribuiria lendo o texto — sem olhar o veredito do modelo, que não está
neste arquivo. Se algo não cabe em nenhum eixo, marque `livre` e descreva em
`temas`. Salve o arquivo quando terminar; o script de métricas
(`scripts/auditoria_acuracia.py metricas`) lê os `[x]` daqui.

**Os 10 eixos, para referência rápida** (definição completa em
`scripts/classificar_10.py`, bloco `SYSTEM`):
ritmo · atuacao · direcao_imagem · roteiro_estrutura · som_trilha ·
tom_atmosfera · impacto_emocional · comparacoes · expectativa ·
critica_social.

O veredito do modelo NÃO está neste arquivo — está em
`gabarito_modelo.json`, separado de propósito, para que nada aqui enviese a
leitura antes do julgamento.

"""
    blocos = [_bloco_markdown(i + 1, r) for i, r in enumerate(escolhidas)]
    ARQ_LEITURA.write_text(cabecalho + "\n".join(blocos), encoding="utf-8")


def cmd_amostra() -> None:
    SAIDA.mkdir(parents=True, exist_ok=True)
    universo = _carregar_universo()
    rng = random.Random(SEMENTE)
    escolhidas, telemetria = montar_amostra_auditoria(universo, rng)

    # Índice — SEM eixos do modelo, para que este arquivo também possa ser
    # olhado sem risco de enviesar a leitura.
    indice = {
        "semente": SEMENTE, "taxonomia_id": taxonomia_id(),
        "fonte": "votacao-3/consenso.jsonl (classificação por votação de 3 "
                 "passadas, eixo entra se >=2/3)",
        "n": len(escolhidas), "telemetria": telemetria,
        "reviews": [{"ordem": i + 1, "id": r["id"], "slug": r["slug"],
                     "perfil": r["perfil"], "bucket": r["bucket"],
                     "nivel": r["nivel"], "n_chars": r["n_chars"],
                     "estrato": r["estrato"]}
                    for i, r in enumerate(escolhidas)],
    }
    ARQ_INDICE.write_text(json.dumps(indice, ensure_ascii=False, indent=2),
                          encoding="utf-8")

    # Gabarito do modelo — SEPARADO da leitura, propositalmente. `votos`
    # traz a contagem (3/3 ou 2/3) de cada eixo consensual — é o que
    # permite a quebra unanime-vs-maioria da Entrega 3.
    gabarito = {r["id"]: {"eixos": r["eixos"], "votos": _votos_minimos(r),
                          "confianca": _classe_confianca(r),
                          "eixos_por_passe": r.get("eixos_por_passe", [])}
                for r in escolhidas}
    ARQ_GABARITO.write_text(json.dumps(gabarito, ensure_ascii=False, indent=2),
                            encoding="utf-8")

    escrever_leitura_md(escolhidas)

    print(f"amostra: {len(escolhidas)}/{N_AMOSTRA} · semente {SEMENTE}")
    print(f"  por estrato: {telemetria['composicao_por_estrato']}")
    print(f"  por bucket: {telemetria['composicao_por_bucket']}")
    print(f"  por perfil: {telemetria['composicao_por_perfil']}")
    print(f"  por n_eixos: {telemetria['composicao_por_n_eixos_grupo']}")
    print(f"  por confiança: {telemetria['composicao_por_confianca']}")
    if telemetria["deficits_por_estrato"]:
        print(f"  DÉFICITS (estrato sem material suficiente): "
              f"{telemetria['deficits_por_estrato']}")
    print(f"→ {ARQ_LEITURA.relative_to(RAIZ)} (leia e anote)")
    print(f"→ {ARQ_INDICE.relative_to(RAIZ)} (índice, sem veredito)")
    print(f"→ {ARQ_GABARITO.relative_to(RAIZ)} (veredito do modelo — não abrir "
          f"antes de anotar)")


# ===========================================================================
# Entrega 2 — métricas (script pronto; NÃO chamado por `amostra`/`estabilidade`)
# ===========================================================================

_RE_BLOCO = re.compile(
    r"^### #(\d+) · `([^`]+)` · .+$", re.MULTILINE)
# Aceita os DOIS marcadores de lista do markdown (`-` e `*`): um reformatador
# de markdown troca `-` por `*` sem avisar, e a v1 deste parser só reconhecia
# `-` — as 1100 linhas de checkbox viravam "nenhum eixo marcado" em silêncio.
_RE_CHECK = re.compile(r"^[-*] \[([ xX])\] (\S+)(?: — temas: (.*))?$", re.MULTILINE)


def ler_anotacoes_humanas(caminho: Path = ARQ_LEITURA) -> dict[str, dict]:
    """Parseia `leitura.md` de volta para `{id: {eixos, temas_livres}}`.

    Robustez deliberada: uma linha de checkbox mal editada (esqueceu o `x`,
    digitou `[X]` maiúsculo) não derruba o parser inteiro — cada bloco é
    parseado independentemente, e um bloco sem NENHUM `[x]` marcado gera
    `eixos: []` (revisão pendente ou julgamento genuíno de zero eixos —
    ambíguo por construção do formato, registrado como aviso, não erro).
    """
    texto = caminho.read_text(encoding="utf-8")
    marcadores = list(_RE_BLOCO.finditer(texto))
    anotacoes: dict[str, dict] = {}
    avisos: list[str] = []
    for i, m in enumerate(marcadores):
        rid = m.group(2)
        fim = marcadores[i + 1].start() if i + 1 < len(marcadores) else len(texto)
        trecho = texto[m.end():fim]
        eixos, livre_marcado, temas = [], False, []
        for cm in _RE_CHECK.finditer(trecho):
            marcado = cm.group(1).strip().lower() == "x"
            nome = cm.group(2)
            if nome == "livre":
                if marcado:
                    livre_marcado = True
                    bruto = (cm.group(3) or "").strip()
                    if bruto:
                        temas = [t.strip() for t in bruto.split(",") if t.strip()]
            elif marcado:
                if nome not in EIXOS:
                    avisos.append(f"{rid}: checkbox com nome desconhecido: {nome!r}")
                    continue
                eixos.append(nome)
        if livre_marcado:
            eixos.append("livre")
        if not eixos:
            avisos.append(f"{rid}: nenhum eixo marcado (zero eixos ou "
                          f"anotação pendente — confira à mão)")
        anotacoes[rid] = {"eixos": sorted(set(eixos)), "temas_livres": temas}
    if avisos:
        print(f"[ler_anotacoes_humanas] {len(avisos)} aviso(s):")
        for a in avisos[:20]:
            print(f"  - {a}")
        if len(avisos) > 20:
            print(f"  ... e mais {len(avisos) - 20}")

    # GUARD-RAIL: um arquivo anotado em que NENHUMA review tem marcação não é
    # um resultado ("o humano não viu eixo em nada"), é falha de parsing — o
    # formato do checkbox mudou e o regex deixou de casar. A v1 degradava em
    # silêncio para 100 × `eixos: []` e produzia um relatório inteiro sobre
    # dado vazio. Falhar aqui é barato; analisar o vazio custou uma rodada.
    if anotacoes and not any(a["eixos"] for a in anotacoes.values()):
        n_check = len(_RE_CHECK.findall(texto))
        raise SystemExit(
            f"ERRO DE PARSING: {len(anotacoes)} bloco(s) de review lidos em "
            f"{caminho.name}, e NENHUM tem eixo marcado.\n"
            f"  linhas de checkbox reconhecidas pelo regex: {n_check}\n"
            f"  esperado: linhas no formato `- [x] nome_do_eixo` (ou `* [x] ...`)\n"
            f"Isso quase certamente é o formato do arquivo, não a anotação: um "
            f"arquivo anotado de verdade tem ao menos uma marcação. Confira o "
            f"marcador de lista e o caractere dentro dos colchetes antes de "
            f"rodar as métricas.")
    return anotacoes


def _bucket_n_chars(n: int) -> str:
    if n <= 200:
        return "<=200 (piso)"
    if n <= 400:
        return "201-400"
    if n <= 800:
        return "401-800"
    return "801+"


def calcular_metricas(anotacoes: dict[str, dict]) -> dict:
    """[Entrega 2] Precisão/recall por eixo, quebras por bucket/comprimento/
    n_eixos/CONFIANÇA DO VOTO, concordância exata, e a matriz de confusão
    entre eixos.

    **Quebra por confiança (nova, sobre consenso):** cada review carrega
    `confianca` (`unanime` se todo eixo consensual saiu 3/3, `maioria` se
    ao menos um saiu 2/3, `vazio` se nenhum eixo alcançou consenso) — é a
    pergunta central desta rodada: se `unanime` for acurado e `maioria`
    duvidoso, isso vira régua de confiança publicável junto com a
    frequência agregada.

    **Definição de confusão** (única forma que este script usa a palavra):
    para uma review onde o modelo atribuiu `A` sem confirmação humana (falso
    positivo do modelo) E o humano atribuiu `B` que o modelo perdeu (falso
    negativo do modelo), conta-se um evento `A confundido com B`. Não é uma
    inferência causal — é uma co-ocorrência dentro da MESMA review, a leitura
    mais direta de "quando erra, com o que ele troca".
    """
    indice = json.loads(ARQ_INDICE.read_text(encoding="utf-8"))
    gabarito = json.loads(ARQ_GABARITO.read_text(encoding="utf-8"))
    meta_por_id = {r["id"]: r for r in indice["reviews"]}

    faltando = [rid for rid in gabarito if rid not in anotacoes]
    if faltando:
        print(f"AVISO: {len(faltando)} review(s) do gabarito sem anotação "
              f"humana correspondente — excluídas do cálculo: {faltando[:5]}"
              f"{'...' if len(faltando) > 5 else ''}")

    pares = []  # (id, eixos_modelo, eixos_humano, meta)
    for rid, g in gabarito.items():
        if rid not in anotacoes or rid not in meta_por_id:
            continue
        meta = dict(meta_por_id[rid], confianca=g.get("confianca"))
        pares.append((rid, set(g["eixos"]) - {"livre"},
                      set(anotacoes[rid]["eixos"]) - {"livre"},
                      meta))

    def prf_por_eixo(subset):
        saida = {}
        for e in EIXOS:
            tp = sum(1 for _, m, h, _ in subset if e in m and e in h)
            fp = sum(1 for _, m, h, _ in subset if e in m and e not in h)
            fn = sum(1 for _, m, h, _ in subset if e not in m and e in h)
            precisao = tp / (tp + fp) if (tp + fp) else None
            recall = tp / (tp + fn) if (tp + fn) else None
            f1 = (2 * precisao * recall / (precisao + recall)
                  if precisao and recall else None)
            saida[e] = {"tp": tp, "fp": fp, "fn": fn,
                        "precisao": precisao, "recall": recall, "f1": f1}
        return saida

    def resumo_geral(subset):
        n = len(subset)
        exatos = sum(1 for _, m, h, _ in subset if m == h)
        return {"n": n, "concordancia_exata": exatos / n if n else None,
                "por_eixo": prf_por_eixo(subset)}

    confusao = Counter()
    for _, m, h, _ in pares:
        fps, fns = m - h, h - m
        for a in fps:
            for b in fns:
                confusao[(a, b)] += 1

    por_bucket = {b: resumo_geral([p for p in pares if p[3]["bucket"] == b])
                 for b in BUCKETS}
    por_confianca = {c: resumo_geral([p for p in pares if p[3]["confianca"] == c])
                     for c in ("unanime", "maioria", "vazio")}
    por_comprimento = {}
    for p in pares:
        por_comprimento.setdefault(_bucket_n_chars(p[3]["n_chars"]), []).append(p)
    por_comprimento = {k: resumo_geral(v) for k, v in por_comprimento.items()}
    por_n_eixos_humano = {}
    for p in pares:
        k = len(p[2])
        por_n_eixos_humano.setdefault(k, []).append(p)
    por_n_eixos_humano = {str(k): resumo_geral(v)
                          for k, v in sorted(por_n_eixos_humano.items())}

    return {
        "n_pares": len(pares), "n_gabarito": len(gabarito),
        "n_faltando_anotacao": len(faltando),
        "geral": resumo_geral(pares),
        "por_bucket": por_bucket,
        "por_confianca_voto": por_confianca,
        "por_faixa_n_chars": por_comprimento,
        "por_n_eixos_atribuidos_pelo_humano": por_n_eixos_humano,
        "matriz_confusao_top20": [
            {"modelo_atribuiu": a, "humano_atribuiu": b, "n": n}
            for (a, b), n in confusao.most_common(20)],
        "pares_suspeitos_registrados_a_priori": {
            "impacto_emocional_vs_tom_atmosfera": confusao.get(
                ("impacto_emocional", "tom_atmosfera"), 0)
            + confusao.get(("tom_atmosfera", "impacto_emocional"), 0),
            "expectativa_vs_comparacoes": confusao.get(
                ("expectativa", "comparacoes"), 0)
            + confusao.get(("comparacoes", "expectativa"), 0),
        },
    }


def cmd_metricas() -> None:
    if not ARQ_LEITURA.exists() or not ARQ_GABARITO.exists():
        raise SystemExit(
            f"faltam {ARQ_LEITURA.name}/{ARQ_GABARITO.name} — rode `amostra` "
            f"primeiro e devolva o arquivo anotado.")
    anotacoes = ler_anotacoes_humanas()
    n_pendentes = sum(1 for a in anotacoes.values() if not a["eixos"])
    if n_pendentes:
        print(f"\nAVISO: {n_pendentes} review(s) sem NENHUM eixo marcado — "
              f"confira se é anotação pendente antes de confiar no relatório.\n")
    rel = calcular_metricas(anotacoes)
    ARQ_METRICAS.write_text(json.dumps(rel, ensure_ascii=False, indent=2),
                            encoding="utf-8")
    print(f"n={rel['n_pares']} · concordância exata "
          f"{rel['geral']['concordancia_exata']:.1%}")
    print(f"→ {ARQ_METRICAS.relative_to(RAIZ)}")


# ===========================================================================
# Entrega 3 — estabilidade entre execuções (chamadas LLM reais)
# ===========================================================================

def cmd_estabilidade() -> None:
    """Reclassifica `N_ESTABILIDADE` reviews JÁ classificadas, com o MESMO
    `SYSTEM`/eixos/modelo (nenhum parâmetro de temperatura é passado em
    lugar nenhum do pipeline — reusar `deepseek_resposta` como
    `classificar_10.classificar` já faz é o que garante "mesma
    temperatura": não há override em nenhum dos dois caminhos), e compara o
    conjunto de eixos novo contra o já persistido.

    Independente do julgamento humano — mede quanto da classificação é
    VARIÂNCIA do modelo, não se o modelo está certo. Um número baixo aqui não
    prova acurácia; um número alto é um TETO: nenhuma auditoria humana mede
    melhor do que o modelo é consigo mesmo.
    """
    from dotenv import load_dotenv
    load_dotenv(RAIZ / ".env")

    SAIDA.mkdir(parents=True, exist_ok=True)
    universo = _carregar_universo()
    rng = random.Random(f"{SEMENTE}:estabilidade")
    amostra = rng.sample(universo, min(N_ESTABILIDADE, len(universo)))

    ja_feitas = set()
    if ARQ_ESTABILIDADE_BRUTO.exists():
        for linha in ARQ_ESTABILIDADE_BRUTO.read_text(encoding="utf-8").splitlines():
            if linha.strip():
                r = json.loads(linha)
                if r.get("ok"):
                    ja_feitas.add(r["id"])
    pendentes = [r for r in amostra if r["id"] not in ja_feitas]
    print(f"estabilidade: {len(amostra)} sorteadas · {len(ja_feitas)} já feitas "
          f"· {len(pendentes)} pendentes")

    if pendentes:
        client = deepseek_client()
        lock, contador, t0 = Lock(), [0], time.time()
        saida = ARQ_ESTABILIDADE_BRUTO.open("a", encoding="utf-8")

        def tarefa(review: dict) -> None:
            erro = ""
            for tentativa in range(3):
                try:
                    resp = deepseek_resposta(
                        SYSTEM,
                        f"Review (nota {review['nivel']} de 5 estrelas):\n\n"
                        f"{review['texto']}",
                        MODELO, max_tokens=300, json_mode=True, client=client)
                    data = json.loads(resp.choices[0].message.content)
                    eixos, livres, invalidos = _normalizar(data)
                    registro = {
                        "ok": True, "id": review["id"], "slug": review["slug"],
                        "bucket": review["bucket"], "n_chars": review["n_chars"],
                        "eixos_original": review["eixos"],
                        "eixos_reclassificado": eixos,
                        "temas_livres_reclassificado": livres,
                        "eixos_invalidos_reclassificado": invalidos,
                        "uso": deepseek_uso(resp),
                    }
                    break
                except Exception as e:  # noqa: BLE001
                    erro = f"{type(e).__name__}: {e}"
                    time.sleep(2 * (tentativa + 1))
            else:
                registro = {"ok": False, "id": review["id"], "erro": erro}
            with lock:
                saida.write(json.dumps(registro, ensure_ascii=False) + "\n")
                saida.flush()
                contador[0] += 1
                if contador[0] % 50 == 0 or contador[0] == len(pendentes):
                    dt = time.time() - t0
                    print(f"  {contador[0]}/{len(pendentes)} · {dt:.0f}s", flush=True)

        with ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(tarefa, pendentes))
        saida.close()

    # --- relatório ---
    regs = []
    for linha in ARQ_ESTABILIDADE_BRUTO.read_text(encoding="utf-8").splitlines():
        if linha.strip():
            r = json.loads(linha)
            if r.get("ok"):
                regs.append(r)
    # Aplica o MESMO reparo de nome malformado, para não confundir
    # "instabilidade real" com "typo de digitação do modelo".
    for r in regs:
        eixos = list(r["eixos_reclassificado"])
        for bruto in r.get("eixos_invalidos_reclassificado", []):
            alvo = recuperar_eixo(bruto)
            if alvo and alvo not in eixos:
                eixos.append(alvo)
        r["eixos_reclassificado"] = sorted(set(eixos))

    meta_por_id = {r["id"]: r for r in universo}
    identicos = sum(1 for r in regs
                    if set(r["eixos_original"]) == set(r["eixos_reclassificado"]))
    oscilacao_por_eixo = Counter()
    for r in regs:
        a, b = set(r["eixos_original"]), set(r["eixos_reclassificado"])
        for e in a ^ b:  # diferença simétrica: entrou ou saiu
            oscilacao_por_eixo[e] += 1

    def _grupo(r):
        return meta_por_id.get(r["id"], {}).get("n_chars")

    por_faixa = defaultdict(lambda: [0, 0])  # [identicos, total]
    por_n_eixos = defaultdict(lambda: [0, 0])
    for r in regs:
        nc = r.get("n_chars") or 0
        faixa = _bucket_n_chars(nc)
        idem = set(r["eixos_original"]) == set(r["eixos_reclassificado"])
        por_faixa[faixa][0] += int(idem)
        por_faixa[faixa][1] += 1
        n_orig = len([e for e in r["eixos_original"] if e != "livre"])
        gk = ("0" if n_orig == 0 else "1-2" if n_orig <= 2 else
              "3-4" if n_orig <= 4 else "5-6" if n_orig <= 6 else "7+")
        por_n_eixos[gk][0] += int(idem)
        por_n_eixos[gk][1] += 1

    uso = Counter()
    for r in regs:
        for k, v in r.get("uso", {}).items():
            uso[k] += v
    from classificar_10 import PRECO_ENTRADA_HIT, PRECO_ENTRADA_MISS, PRECO_SAIDA
    custo = (uso["cache_miss_tokens"] * PRECO_ENTRADA_MISS
             + uso["cache_hit_tokens"] * PRECO_ENTRADA_HIT
             + uso["completion_tokens"] * PRECO_SAIDA)

    rel = {
        "n_reclassificadas": len(regs),
        "fracao_identica": identicos / len(regs) if regs else None,
        "eixos_que_mais_oscilam": dict(oscilacao_por_eixo.most_common(10)),
        "identica_por_faixa_n_chars": {
            k: {"identicas": v[0], "n": v[1], "fracao": v[0] / v[1]}
            for k, v in sorted(por_faixa.items())},
        "identica_por_n_eixos_original": {
            k: {"identicas": v[0], "n": v[1], "fracao": v[0] / v[1]}
            for k, v in sorted(por_n_eixos.items())},
        "custo_usd": custo,
    }
    ARQ_ESTABILIDADE_RELATORIO.write_text(
        json.dumps(rel, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nfração idêntica: {rel['fracao_identica']:.1%} (n={len(regs)})")
    print(f"custo: US$ {custo:.4f}")
    print(f"→ {ARQ_ESTABILIDADE_RELATORIO.relative_to(RAIZ)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("etapa", choices=["amostra", "metricas", "estabilidade"])
    args = ap.parse_args()

    if args.etapa == "amostra":
        cmd_amostra()
    elif args.etapa == "metricas":
        cmd_metricas()
    else:
        cmd_estabilidade()
