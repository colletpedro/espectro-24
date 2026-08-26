"""[GATE] Retro-fit da taxonomia de eixos — MEDIÇÃO, zero mudança de schema.

Mede se a taxonomia FECHADA de eixos proposta para a fase de síntese cobre o
que as reviews reais dizem, ANTES de o schema do JSON de resultado e o layout
do frontend serem commitados.

Arquitetura (a mesma já validada no resto do projeto): **o modelo classifica
review a review, o CÓDIGO soma**. O LLM nunca vê mais de uma review por
chamada, nunca recebe uma contagem e nunca devolve uma — devolve só a lista
de eixos que AQUELA review menciona. Toda frequência, fração e lift deste
relatório é aritmética de `collections.Counter` sobre essas listas.

Este script é DESCARTÁVEL: não integra o pipeline de produção, não escreve em
`resultado/<slug>.json`, não toca frontend nem schema. Escreve só dentro de
`resultado/gate-taxonomia/`.

Etapas (cada uma reexecutável; a 2 tem checkpoint em arquivo):

  1. `amostra`   — seleção determinística de filmes e reviews (sem LLM)
  2. `classificar` — 1 chamada de LLM por review, com resume via JSONL
  3. `relatorio` — agregação + as 5 entregas do gate (sem LLM)

Uso:
    python scripts/gate_taxonomia.py amostra
    python scripts/gate_taxonomia.py classificar [--limite N]
    python scripts/gate_taxonomia.py relatorio
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
import time
import unicodedata
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Lock

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from espectro24.bruto import carregar  # noqa: E402
from espectro24.buckets import FRONTEIRAS  # noqa: E402
from espectro24.selecao import selecionar  # noqa: E402
from espectro24.synthesize import (  # noqa: E402
    deepseek_client,
    deepseek_resposta,
    deepseek_uso,
    telemetria_retentativa_llm,
)

SAIDA = RAIZ / "resultado" / "gate-taxonomia"
ARQ_AMOSTRA = SAIDA / "amostra.json"
ARQ_CLASSIF = SAIDA / "classificacoes.jsonl"
ARQ_FAMILIAS = SAIDA / "familias.json"
ARQ_TRIAGEM = SAIDA / "triagem_so_livre.jsonl"
ARQ_RELATORIO = SAIDA / "relatorio.json"

# --- Parâmetros da amostra (registrados no JSON de saída) ------------------
SEMENTE = 20260808          # semente global; cada sorteio deriva a sua daqui
N_FILMES = 15
N_REVIEWS_POR_BUCKET = 20
MODELO = "deepseek-v4-flash"
CONCORRENCIA = 8
# [v1.9.25] `MAX_TENTATIVAS` REMOVIDO: retentativa de transporte vive no
# adaptador (`synthesize._com_retentativa`, §3[D]), com backoff exponencial
# e jitter. Os laços locais retentavam também erro de CONTEÚDO e, depois da
# v1.9.25, empilhariam sobre a do adaptador.

# --- A taxonomia sob teste -------------------------------------------------
EIXOS = (
    "ritmo",
    "atuacao",
    "direcao_imagem",
    "roteiro_estrutura",
    "som_trilha",
    "tom_atmosfera",
    "impacto_emocional",
    "comparacoes",
)
EIXOS_VALIDOS = set(EIXOS) | {"livre"}

# Preços DeepSeek em USD por 1M de tokens (config.py, v1.8.0).
PRECO_ENTRADA_MISS = 0.14 / 1_000_000
PRECO_ENTRADA_HIT = 0.0028 / 1_000_000
PRECO_SAIDA = 0.28 / 1_000_000


# ===========================================================================
# ETAPA 1 — AMOSTRA
# ===========================================================================

def perfil_de(slug: str, hist: dict[float, int]) -> str:
    """Perfil de catálogo de um filme, derivado do HISTOGRAMA público — não da
    intenção com que ele entrou na lista de coleta.

    Regras, aplicadas nesta ordem de precedência (cada filme cai em
    exatamente um perfil):

      obscuro   — menos de 10.000 notas no total. É a cauda de popularidade,
                  onde a amostra por bucket é pequena e o vocabulário das
                  reviews é menos padronizado.
      invertido — negativas >= 20% das notas. Distribuição virada; o bucket
                  dominante é o negativo ou o morno.
      divisivo  — mornos >= 20% das notas. Sem dominância clara.
      arthouse  — pertence à lista declarada de não-anglófono/arthouse do
                  catálogo (`_ARTHOUSE`). É o único critério que NÃO sai do
                  histograma: "arthouse" não é uma propriedade da distribuição
                  de notas, e fingir derivá-la dela seria falso rigor.
      aclamado  — o resto (positivas dominantes, filme popular).
    """
    total = sum(hist.values())
    share = lambda lo, hi: 100 * sum(  # noqa: E731
        v for k, v in hist.items() if lo <= k <= hi) / total
    if total < 10_000:
        return "obscuro"
    if share(*FRONTEIRAS["negativas"]) >= 20:
        return "invertido"
    if share(*FRONTEIRAS["medianas"]) >= 20:
        return "divisivo"
    if slug in _ARTHOUSE:
        return "arthouse"
    return "aclamado"


# Não-anglófono / arthouse. Os 4 primeiros são a rubrica declarada em
# `dados/lote-slugs.txt`; os 3 seguintes entraram no catálogo antes do lote e
# se encaixam na mesma rubrica (dois deles não-anglófonos, o terceiro
# japonês de gênero).
_ARTHOUSE = {
    "perfect-days-2023", "anatomy-of-a-fall", "aftersun", "im-still-here-2024",
    "cidade-de-deus", "cure", "parasite-2019",
}

# Quantos filmes por perfil. `obscuro` e `invertido` entram INTEIROS (são
# raros no catálogo — 1 e 4 filmes; sortear dentro deles jogaria fora
# justamente o material que mais pode reprovar a taxonomia). Os outros três
# são sorteados. `arthouse` leva uma vaga a mais que `divisivo`/`aclamado`
# pelo mesmo motivo: é o perfil onde a hipótese "a taxonomia funciona" é mais
# frágil a priori.
COTA_POR_PERFIL = {
    "obscuro": None,      # None = todos
    "invertido": None,    # None = todos
    "arthouse": 4,
    "divisivo": 3,
    "aclamado": 3,
}


def escolher_filmes(raiz_bruto: Path) -> tuple[list[dict], dict]:
    """Escolhe os filmes da amostra. Determinístico dado `SEMENTE`."""
    catalogo = []
    for d in sorted(raiz_bruto.iterdir()):
        if not (d / "meta.json").exists():
            continue
        meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
        hist = {float(k): v for k, v in meta.get("histograma_bruto", {}).items()}
        if not hist:
            continue
        catalogo.append({"slug": d.name, "perfil": perfil_de(d.name, hist),
                         "total_notas": sum(hist.values())})

    por_perfil = defaultdict(list)
    for f in catalogo:
        por_perfil[f["perfil"]].append(f)

    escolhidos = []
    for perfil, cota in COTA_POR_PERFIL.items():
        pool = sorted(por_perfil.get(perfil, []), key=lambda f: f["slug"])
        if cota is None or cota >= len(pool):
            escolhidos.extend(pool)
        else:
            rng = random.Random(f"{SEMENTE}:filmes:{perfil}")
            escolhidos.extend(sorted(rng.sample(pool, cota),
                                     key=lambda f: f["slug"]))
    escolhidos.sort(key=lambda f: (f["perfil"], f["slug"]))
    censo = {p: len(v) for p, v in sorted(por_perfil.items())}
    return escolhidos, censo


def montar_amostra() -> dict:
    filmes, censo = escolher_filmes(RAIZ / "dados" / "bruto")
    itens, resumo = [], []
    for f in filmes:
        meta, todas = carregar(f["slug"])
        hist = {float(k): v for k, v in meta.get("histograma_bruto", {}).items()}
        # Parâmetros de PRODUÇÃO — a amostra sai do mesmo pool que iria à
        # síntese, não de um pool inventado para o gate.
        sel = selecionar(todas, hist)
        linha = {"slug": f["slug"], "perfil": f["perfil"],
                 "total_notas": f["total_notas"], "por_bucket": {}}
        for nome, bucket in sel.items():
            validas = [r for n in sorted(bucket.niveis) for r in bucket.niveis[n].validas]
            rng = random.Random(f"{SEMENTE}:{f['slug']}:{nome}")
            k = min(N_REVIEWS_POR_BUCKET, len(validas))
            escolhidas = rng.sample(validas, k) if k else []
            escolhidas.sort(key=lambda r: r.id)
            linha["por_bucket"][nome] = {"pool": len(validas), "amostrado": k}
            for r in escolhidas:
                itens.append({
                    "slug": f["slug"], "perfil": f["perfil"], "bucket": nome,
                    "id": r.id, "nivel": r.nivel, "n_chars": r.n_chars,
                    "texto": r.texto,
                })
        resumo.append(linha)

    return {
        "semente": SEMENTE,
        "criterio_filmes": {
            "perfil": "derivado do histograma público (ver `perfil_de`)",
            "cotas": {k: (v if v is not None else "todos")
                      for k, v in COTA_POR_PERFIL.items()},
            "censo_do_catalogo_por_perfil": censo,
        },
        "criterio_reviews": (
            f"selecao.selecionar() com parâmetros de produção (cota 40/bucket, "
            f"min_chars 150, cascata, spoiler excluído); sorteio sem reposição "
            f"de até {N_REVIEWS_POR_BUCKET} por bucket, RNG semeado por "
            f"'{SEMENTE}:<slug>:<bucket>'"),
        "n_reviews_por_bucket_alvo": N_REVIEWS_POR_BUCKET,
        "taxonomia": list(EIXOS),
        "filmes": resumo,
        "reviews": itens,
    }


# ===========================================================================
# ETAPA 2 — CLASSIFICAÇÃO (1 chamada por review)
# ===========================================================================

SYSTEM = """Você classifica UMA review de cinema por vez segundo uma taxonomia fechada de EIXOS.

Os eixos disponíveis são exatamente estes:

- ritmo: velocidade, duração, arrasta/prende, edição no sentido de andamento, tédio ou tensão sustentada.
- atuacao: desempenho do elenco, performance de um ator ou atriz, elenco, direção de atores.
- direcao_imagem: fotografia, planos, cor, luz, composição, cenário, figurino, efeitos visuais, direção no sentido visual.
- roteiro_estrutura: história, enredo, estrutura, diálogos, personagens, final, coerência, previsibilidade.
- som_trilha: trilha sonora, música, som, mixagem, silêncio, canções.
- tom_atmosfera: clima, atmosfera, humor, registro, se é sério ou cômico, sensação de estranheza, ambiência.
- impacto_emocional: o efeito que causou em quem escreveu — chorou, se arrepiou, saiu abalado, se identificou, ficou indiferente.
- comparacoes: comparação com outro filme, outra obra, outro diretor, com o livro, com a franquia, com o trabalho anterior do mesmo autor.

REGRAS:
1. Atribua TODOS os eixos que a review realmente menciona, e SÓ esses. Uma review pode ter vários eixos, ou um só.
2. Seja ESTRITO. Só atribua um eixo se a review disser algo sobre ele. Nota alta ou entusiasmo genérico ("obra-prima", "amei", "5 estrelas") NÃO é impacto_emocional nem nenhum outro eixo — é elogio sem eixo.
3. Se a review fala de algo que não cabe em NENHUM eixo acima, inclua "livre" na lista.
4. Sempre que incluir "livre", escreva em `temas_livres` de 1 a 2 rótulos curtos (2 a 4 palavras, em português, minúsculas) descrevendo o que não coube. Exemplos de forma: "discurso politico do filme", "reacao da plateia no cinema", "expectativa antes de assistir".
5. Se a review não diz nada classificável em nenhum eixo (só xingamento, só piada solta, só emoji, só nota), devolva `["livre"]` com um tema livre que descreva o que ela é.
6. NÃO conte nada. NÃO some. NÃO comente. Devolva só o JSON.

Responda APENAS com um objeto JSON, sem cercas de código, exatamente neste formato:
{"eixos": ["..."], "temas_livres": ["..."]}"""


def _mensagem(review: dict) -> str:
    return (f"Review (nota {review['nivel']} de 5 estrelas):\n\n"
            f"{review['texto']}")


def _chamar_json(client, system: str, user: str, max_tokens: int) -> tuple[dict, dict]:
    """UMA chamada JSON pelo ADAPTADOR (§3[D], guard-rail da v1.9.4).

    Este script foi o caso que motivou o guard-rail: a primeira versão
    instanciava o SDK por conta própria e, sem `thinking: disabled`, 8 das 12
    primeiras chamadas voltaram com `content` VAZIO — o raciocínio consumiu o
    orçamento de `max_tokens` inteiro antes do JSON, a MESMA causa raiz que
    `synthesize.deepseek_client_call` documenta desde a v1.8.0. Agora o
    transporte é o do adaptador, e `thinking: disabled` não pode se perder
    aqui nem em nenhum script futuro.
    """
    resp = deepseek_resposta(system, user, MODELO, max_tokens=max_tokens,
                             json_mode=True, client=client)
    texto = (resp.choices[0].message.content or "").strip()
    if texto.startswith("```"):
        texto = texto.split("\n", 1)[1] if "\n" in texto else texto
        texto = texto.rsplit("```", 1)[0]
        if texto.lstrip().lower().startswith("json"):
            texto = texto.lstrip()[4:]
    return json.loads(texto.strip()), deepseek_uso(resp)


def _chamar(client, review: dict) -> tuple[dict, dict]:
    return _chamar_json(client, SYSTEM, _mensagem(review), 300)


def _normalizar(data: dict) -> tuple[list[str], list[str], list[str]]:
    """Devolve (eixos_válidos, temas_livres, eixos_descartados).

    Um eixo inventado pelo modelo é DESCARTADO e contado — não vira `livre`
    nem entra na frequência. Silenciar essa contagem seria esconder o único
    sinal de que o modelo não está respeitando a taxonomia fechada."""
    crus = data.get("eixos") or []
    if isinstance(crus, str):
        crus = [crus]
    eixos, invalidos = [], []
    for e in crus:
        e = str(e).strip().lower()
        (eixos if e in EIXOS_VALIDOS else invalidos).append(e)
    livres = data.get("temas_livres") or []
    if isinstance(livres, str):
        livres = [livres]
    livres = [str(t).strip().lower() for t in livres if str(t).strip()]
    return sorted(set(eixos)), livres, invalidos


def classificar(limite: int | None = None) -> None:
    from dotenv import load_dotenv
    load_dotenv(RAIZ / ".env")

    amostra = json.loads(ARQ_AMOSTRA.read_text(encoding="utf-8"))
    feitos = set()
    if ARQ_CLASSIF.exists():
        for linha in ARQ_CLASSIF.read_text(encoding="utf-8").splitlines():
            if linha.strip():
                r = json.loads(linha)
                if r.get("ok"):
                    feitos.add((r["slug"], r["bucket"], r["id"]))

    pendentes = [r for r in amostra["reviews"]
                 if (r["slug"], r["bucket"], r["id"]) not in feitos]
    if limite:
        pendentes = pendentes[:limite]
    print(f"{len(feitos)} já classificadas · {len(pendentes)} pendentes")
    if not pendentes:
        return

    client = deepseek_client()
    lock, contador, t0 = Lock(), [0], time.time()
    falhas = [0]
    saida = ARQ_CLASSIF.open("a", encoding="utf-8")

    def tarefa(review: dict) -> None:
        # [v1.9.25, §3[D]] SEM laço de retentativa próprio — o adaptador
        # retenta TRANSPORTE dentro de `deepseek_resposta`, e um laço aqui
        # empilharia 3×3. O `except` só REGISTRA e deixa o lote seguir.
        try:
            data, uso = _chamar(client, review)
            eixos, livres, invalidos = _normalizar(data)
            registro = {
                "ok": True, "slug": review["slug"], "perfil": review["perfil"],
                "bucket": review["bucket"], "id": review["id"],
                "nivel": review["nivel"], "n_chars": review["n_chars"],
                "eixos": eixos, "temas_livres": livres,
                "eixos_invalidos": invalidos, "uso": uso,
            }
        except Exception as e:  # noqa: BLE001
            registro = {"ok": False, "slug": review["slug"],
                        "perfil": review["perfil"], "bucket": review["bucket"],
                        "id": review["id"], "erro": f"{type(e).__name__}: {e}"}
        with lock:
            saida.write(json.dumps(registro, ensure_ascii=False) + "\n")
            saida.flush()
            contador[0] += 1
            if not registro["ok"]:
                falhas[0] += 1
            if contador[0] % 25 == 0 or contador[0] == len(pendentes):
                dt = time.time() - t0
                print(f"  {contador[0]}/{len(pendentes)} · {dt:.0f}s "
                      f"· {contador[0]/dt:.1f}/s", flush=True)

    with ThreadPoolExecutor(max_workers=CONCORRENCIA) as pool:
        list(pool.map(tarefa, pendentes))
    saida.close()
    # [v1.9.25] Taxa VISÍVEL — o consumidor pula `ok: False` em silêncio.
    tel = telemetria_retentativa_llm()
    print(f"  falhas (ok=False): {falhas[0]}/{len(pendentes)} · retentativas "
          f"de transporte no adaptador: {tel['n_retentativas']}"
          + (f" {tel['por_tipo']}" if tel["por_tipo"] else ""))


# ===========================================================================
# ETAPA 2b — FAMÍLIAS DE TEMA LIVRE (Entrega 3)
# ===========================================================================
# O agrupamento lexical determinístico (`_agrupar_temas`, abaixo) responde mal
# à pergunta da Entrega 3: ele fragmenta "expectativa antes de assistir",
# "expectativa do espectador" e "expectativa vs realidade" em três grupos,
# porque não compartilham vocabulário suficiente. Como a pergunta é
# SEMÂNTICA ("o que está faltando na taxonomia?"), a camada de família usa o
# LLM — mas sob a MESMA disciplina do resto: o modelo julga UM rótulo por
# chamada e nunca vê contagem nenhuma; o CÓDIGO soma ocorrências e conta
# filmes distintos. As duas camadas são publicadas lado a lado no relatório.

SYSTEM_FAMILIAS = """Você recebe uma lista de rótulos curtos. Cada rótulo descreve um assunto que apareceu numa review de cinema e que NÃO coube em nenhum destes eixos: ritmo, atuação, direção/imagem, roteiro/estrutura, som/trilha, tom/atmosfera, impacto emocional, comparações com outras obras.

Sua tarefa: propor de 8 a 14 FAMÍLIAS que agrupem esses rótulos por assunto.

REGRAS:
1. Cada família deve ser um assunto coerente e nomeável, no nível de generalidade de um eixo (ex.: "ritmo", "atuação"), não de um rótulo individual.
2. Nomeie cada família com um identificador em snake_case e escreva uma definição de uma frase.
3. Inclua sempre, como última família, `outros` — para rótulo que não pertença a nenhuma das outras.
4. NÃO conte nada, NÃO ordene por frequência, NÃO comente.

Responda APENAS com JSON, neste formato:
{"familias": [{"nome": "...", "definicao": "..."}]}"""


def _system_atribuicao(familias: list[dict]) -> str:
    linhas = "\n".join(f"- {f['nome']}: {f['definicao']}" for f in familias)
    return f"""Você atribui UM rótulo de assunto a exatamente UMA família, de uma lista fechada.

Famílias disponíveis:
{linhas}

REGRAS:
1. Escolha exatamente uma família. Se nenhuma servir, use `outros`.
2. Não invente família nova. Não comente.

Responda APENAS com JSON: {{"familia": "..."}}"""


def _rotulos_distintos() -> list[str]:
    rotulos = set()
    for linha in ARQ_CLASSIF.read_text(encoding="utf-8").splitlines():
        if linha.strip():
            r = json.loads(linha)
            if r.get("ok"):
                rotulos.update(r.get("temas_livres", []))
    return sorted(rotulos)


def familias() -> None:
    from dotenv import load_dotenv
    load_dotenv(RAIZ / ".env")
    client = deepseek_client()

    rotulos = _rotulos_distintos()
    print(f"{len(rotulos)} rótulos distintos")

    def chamar(system: str, user: str, max_tokens: int) -> tuple[dict, dict]:
        # [v1.9.25, §3[D]] O laço de retentativa saiu: o adaptador já retenta
        # TRANSPORTE. Este caminho SEMPRE propagou o erro na última tentativa
        # (`raise`), então remover o laço não muda o contrato — só deixa de
        # repetir chamada por erro de CONTEÚDO e de empilhar sobre o
        # adaptador.
        return _chamar_json(client, system, user, max_tokens)

    # Passo 1 — proposta das famílias. A lista vai em ordem ALFABÉTICA e sem
    # contagem: o modelo não pode inferir frequência daqui.
    prop, uso1 = chamar(SYSTEM_FAMILIAS,
                        "Rótulos:\n" + "\n".join(f"- {r}" for r in rotulos),
                        2000)
    fams = prop["familias"]
    nomes = {f["nome"] for f in fams}
    print("famílias propostas:", ", ".join(sorted(nomes)))

    # Passo 2 — atribuição, UM rótulo por chamada.
    system = _system_atribuicao(fams)
    atribuicao: dict[str, str] = {}
    uso = Counter(uso1)
    lock = Lock()

    def tarefa(rotulo: str) -> None:
        data, u = chamar(system, f"Rótulo: {rotulo}", 60)
        nome = str(data.get("familia", "")).strip().lower()
        with lock:
            atribuicao[rotulo] = nome if nome in nomes else "outros"
            for k, v in u.items():
                uso[k] += v

    with ThreadPoolExecutor(max_workers=CONCORRENCIA) as pool:
        list(pool.map(tarefa, rotulos))

    ARQ_FAMILIAS.write_text(json.dumps(
        {"familias": fams, "atribuicao": atribuicao, "uso_tokens": dict(uso)},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"→ {ARQ_FAMILIAS.relative_to(RAIZ)}")


# ===========================================================================
# ETAPA 2c — TRIAGEM DAS REVIEWS QUE CAÍRAM SÓ EM `livre`
# ===========================================================================
# MEDIÇÃO SUPLEMENTAR, fora do que o gate pediu — mas decisiva para ler o
# número dele. `fracao_livre` mistura duas coisas muito diferentes:
#
#   (i)  a review DIZ algo sobre o filme, e a taxonomia não tem eixo para
#        isso — é lacuna de taxonomia, o que a Entrega 3 quer descobrir;
#   (ii) a review não diz nada avaliável sobre o filme (piada solta, citação
#        de diálogo, "assisti pra entender o outro filme", emoji) — nesse
#        caso nenhum eixo, existente ou futuro, a salvaria.
#
# Nenhum eixo novo reduz (ii). Tratá-la como se fosse (i) inflaria a
# `fracao_livre` contra uma taxonomia que não tem culpa. Esta etapa separa as
# duas — mesma disciplina de sempre: uma review por chamada, o código soma.

SYSTEM_TRIAGEM = """Você recebe UMA review de cinema e responde a UMA pergunta.

A pergunta: esta review diz algo AVALIÁVEL sobre o filme em si — sobre o que ele é, faz, mostra ou provoca?

Responda `avaliavel` se a review comenta qualquer coisa do filme: história, personagens, atores, imagem, som, ritmo, clima, mensagem, o efeito que causou, comparação com outra obra, contexto de produção, crítica ao que ele representa.

Responda `sem_conteudo` se a review NÃO diz nada sobre o filme: só uma piada, só um xingamento sem objeto, só uma citação de diálogo sem comentário, só emoji, só nota, só o relato de em que circunstância assistiu, ou só uma observação sobre a própria pessoa que escreveu.

Na dúvida, responda `avaliavel`.

Responda APENAS com JSON: {"veredito": "avaliavel"} ou {"veredito": "sem_conteudo"}"""


def triagem() -> None:
    from dotenv import load_dotenv
    load_dotenv(RAIZ / ".env")

    amostra = json.loads(ARQ_AMOSTRA.read_text(encoding="utf-8"))
    textos = {(r["slug"], r["bucket"], r["id"]): r["texto"]
              for r in amostra["reviews"]}
    alvos = []
    for linha in ARQ_CLASSIF.read_text(encoding="utf-8").splitlines():
        if not linha.strip():
            continue
        r = json.loads(linha)
        if r.get("ok") and r["eixos"] == ["livre"]:
            alvos.append(r)

    feitos = set()
    if ARQ_TRIAGEM.exists():
        for linha in ARQ_TRIAGEM.read_text(encoding="utf-8").splitlines():
            if linha.strip():
                t = json.loads(linha)
                feitos.add((t["slug"], t["bucket"], t["id"]))
    alvos = [a for a in alvos if (a["slug"], a["bucket"], a["id"]) not in feitos]
    print(f"{len(alvos)} reviews só-livre a triar")
    if not alvos:
        return

    client = deepseek_client()
    saida = ARQ_TRIAGEM.open("a", encoding="utf-8")
    lock = Lock()

    def tarefa(r: dict) -> None:
        # [v1.9.25, §3[D]] Idem: laço removido, contrato preservado (este
        # caminho já propagava o erro na última tentativa).
        texto = textos[(r["slug"], r["bucket"], r["id"])]
        data, u = _chamar_json(client, SYSTEM_TRIAGEM,
                               f"Review:\n\n{texto}", 40)
        v = data.get("veredito")
        reg = {"slug": r["slug"], "perfil": r["perfil"],
               "bucket": r["bucket"], "id": r["id"],
               "veredito": v if v in ("avaliavel", "sem_conteudo") else "avaliavel",
               "uso": u}
        with lock:
            saida.write(json.dumps(reg, ensure_ascii=False) + "\n")
            saida.flush()

    with ThreadPoolExecutor(max_workers=CONCORRENCIA) as pool:
        list(pool.map(tarefa, alvos))
    saida.close()
    print(f"→ {ARQ_TRIAGEM.relative_to(RAIZ)}")


# ===========================================================================
# ETAPA 3 — RELATÓRIO (aritmética pura; o LLM não participa)
# ===========================================================================

_STOP = {"do", "da", "de", "dos", "das", "o", "a", "os", "as", "no", "na",
         "nos", "nas", "e", "em", "um", "uma", "ao", "à", "com", "por",
         "para", "que", "se", "sobre", "filme", "review"}


def _tokens(tema: str) -> frozenset[str]:
    t = unicodedata.normalize("NFKD", tema.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    palavras = [p for p in re.findall(r"[a-z]+", t) if p not in _STOP and len(p) > 2]
    return frozenset(palavras)


def _agrupar_temas(registros: list[dict]) -> list[dict]:
    """Agrupa temas livres por similaridade de vocabulário (Jaccard >= 0.5),
    aglomeração gulosa sobre os temas ordenados por frequência bruta.

    Deliberadamente simples e determinístico: o agrupamento é material de
    LEITURA humana (quais eixos faltam), não uma métrica do gate — nenhum
    número do veredito depende dele."""
    ocorrencias = []
    for r in registros:
        for tema in r.get("temas_livres", []):
            ocorrencias.append((tema, r["slug"], r["bucket"]))

    freq = Counter(t for t, _, _ in ocorrencias)
    grupos: list[dict] = []
    for tema, _ in freq.most_common():
        toks = _tokens(tema)
        if not toks:
            continue
        melhor, melhor_j = None, 0.0
        for g in grupos:
            inter = len(toks & g["tokens"])
            if not inter:
                continue
            j = inter / len(toks | g["tokens"])
            if j > melhor_j:
                melhor, melhor_j = g, j
        if melhor is not None and melhor_j >= 0.5:
            melhor["variantes"].append(tema)
            melhor["tokens"] = melhor["tokens"] | toks
        else:
            grupos.append({"rotulo": tema, "tokens": toks, "variantes": [tema]})

    for g in grupos:
        variantes = set(g["variantes"])
        occ = [o for o in ocorrencias if o[0] in variantes]
        g["n_ocorrencias"] = len(occ)
        g["filmes"] = sorted({s for _, s, _ in occ})
        g["n_filmes"] = len(g["filmes"])
        g["por_bucket"] = dict(Counter(b for _, _, b in occ))
        g["exemplos"] = [v for v, _ in Counter(
            t for t, _, _ in occ).most_common(5)]
        del g["tokens"], g["variantes"]
    grupos.sort(key=lambda g: (-g["n_filmes"], -g["n_ocorrencias"]))
    return grupos


def _familias_agregadas(registros: list[dict],
                        textos: dict[tuple, str] | None = None) -> list[dict]:
    """Agrega as ocorrências de tema livre pelas famílias da etapa 2b.

    Toda contagem aqui é do CÓDIGO: o LLM só disse a que família cada RÓTULO
    pertence, um rótulo por chamada, sem ver frequência nenhuma."""
    if not ARQ_FAMILIAS.exists():
        return []
    dados = json.loads(ARQ_FAMILIAS.read_text(encoding="utf-8"))
    atribuicao, defs = dados["atribuicao"], {
        f["nome"]: f["definicao"] for f in dados["familias"]}

    occ = defaultdict(list)
    exemplos_txt = defaultdict(list)
    for r in registros:
        for tema in r.get("temas_livres", []):
            fam = atribuicao.get(tema, "outros")
            occ[fam].append((tema, r["slug"], r["bucket"], r["eixos"] == ["livre"]))
            if textos and r["eixos"] == ["livre"]:
                t = textos.get((r["slug"], r["bucket"], r["id"]))
                if t:
                    exemplos_txt[fam].append(
                        {"slug": r["slug"], "bucket": r["bucket"], "tema": tema,
                         "texto": t[:260] + ("…" if len(t) > 260 else "")})
    saida = []
    for nome, itens in occ.items():
        filmes = sorted({s for _, s, _, _ in itens})
        saida.append({
            "familia": nome,
            "definicao": defs.get(nome, ""),
            "n_ocorrencias": len(itens),
            "n_filmes": len(filmes),
            "filmes": filmes,
            "n_em_reviews_so_livre": sum(1 for *_, sl in itens if sl),
            "por_bucket": dict(Counter(b for _, _, b, _ in itens)),
            "rotulos_mais_comuns": [t for t, _ in Counter(
                t for t, _, _, _ in itens).most_common(6)],
            # Só de reviews que caíram SÓ em `livre` — são elas que contam
            # para o veredito, e é nelas que a falta de eixo se vê.
            "exemplos_texto": exemplos_txt.get(nome, [])[:4],
        })
    saida.sort(key=lambda f: (-f["n_filmes"], -f["n_ocorrencias"]))
    return saida


def _wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Intervalo de Wilson de 95% para uma proporção. Publicado junto de
    `fracao_livre` porque o critério do gate tem faixas de 5pp e a amostra
    por bucket/perfil é pequena o bastante para o intervalo cruzar uma
    fronteira — ler a estimativa pontual sozinha seria ler menos do que o
    dado diz."""
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    centro = (p + z * z / (2 * n)) / d
    meia = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return (max(0.0, centro - meia), min(1.0, centro + meia))


def _nulo_de_permutacao(regs: list[dict], n_rodadas: int = 2000) -> dict:
    """Quantos pares (filme, eixo) passariam a margem SEM nenhum sinal real?

    Com 20 reviews por bucket, o erro padrão de uma diferença de proporções
    em torno de p=0,3 é ~14,5pp — da ordem da própria margem de 15pp que o
    desenho pretende usar. Contar os pares observados acima da margem, sozinho,
    não distingue sinal de ruído de amostragem.

    O teste: dentro de CADA filme, embaralhar o rótulo de bucket das reviews
    preservando os tamanhos de bucket (o que destrói qualquer associação
    bucket↔eixo mas mantém a frequência global do eixo naquele filme), e
    recontar. A média sobre `n_rodadas` é quantos pares a margem deixa passar
    por acaso. Determinístico: RNG semeado por `SEMENTE`.
    """
    por_filme = defaultdict(list)
    for r in regs:
        por_filme[r["slug"]].append(r)

    filmes = []
    for slug, rs in sorted(por_filme.items()):
        tamanhos = [len([r for r in rs if r["bucket"] == b]) for b in FRONTEIRAS]
        if min(tamanhos) < 15:
            continue
        filmes.append((tamanhos, [[e in r["eixos"] for e in EIXOS] for r in rs]))

    rng = random.Random(f"{SEMENTE}:nulo")
    contagens = {0.15: [], 0.20: []}
    for _ in range(n_rodadas):
        c15 = c20 = 0
        for tamanhos, marcas in filmes:
            ordem = list(range(len(marcas)))
            rng.shuffle(ordem)
            fatias, ini = [], 0
            for t in tamanhos:
                fatias.append(ordem[ini:ini + t])
                ini += t
            for i in range(len(EIXOS)):
                fs = sorted((sum(marcas[j][i] for j in fat) / len(fat))
                            for fat in fatias)
                lift = fs[-1] - fs[-2]
                c15 += lift >= 0.15
                c20 += lift >= 0.20
        contagens[0.15].append(c15)
        contagens[0.20].append(c20)

    def resumo(xs: list[int]) -> dict:
        xs_ord = sorted(xs)
        return {"media": sum(xs) / len(xs),
                "p95": xs_ord[int(0.95 * len(xs_ord))],
                "max": xs_ord[-1]}

    return {
        "n_rodadas": n_rodadas,
        "n_filmes": len(filmes),
        "n_pares": len(filmes) * len(EIXOS),
        "esperado_acima_de_15pp_sob_o_nulo": resumo(contagens[0.15]),
        "esperado_acima_de_20pp_sob_o_nulo": resumo(contagens[0.20]),
    }


def _nulo_parametrico(regs: list[dict], n_por_bucket: int,
                      n_rodadas: int = 2000) -> dict:
    """O mesmo nulo, mas para um tamanho de bucket ARBITRÁRIO.

    Existe por uma razão específica: esta amostra tem 20 reviews por bucket, e
    a produção terá até 40. O nulo de permutação (acima) só sabe falar do
    tamanho que a amostra tem. Aqui, cada (filme, eixo) é reamostrado como
    3 binomiais de tamanho `n_por_bucket` com a frequência GLOBAL observada
    daquele eixo naquele filme — nenhuma associação com bucket, por
    construção — e a contagem acima da margem é recontada.

    Serve para responder se a margem de 15-20pp fica mais defensável quando o
    denominador dobra, sem classificar 2x mais reviews para descobrir.
    """
    por_filme = defaultdict(list)
    for r in regs:
        por_filme[r["slug"]].append(r)
    ps = []
    for slug, rs in sorted(por_filme.items()):
        if min(len([r for r in rs if r["bucket"] == b]) for b in FRONTEIRAS) < 15:
            continue
        ps.append([sum(1 for r in rs if e in r["eixos"]) / len(rs) for e in EIXOS])

    rng = random.Random(f"{SEMENTE}:nulo:{n_por_bucket}")
    c15, c20 = [], []
    for _ in range(n_rodadas):
        a = b = 0
        for freqs in ps:
            for p in freqs:
                fs = sorted(sum(rng.random() < p for _ in range(n_por_bucket))
                            / n_por_bucket for _ in range(3))
                lift = fs[-1] - fs[-2]
                a += lift >= 0.15
                b += lift >= 0.20
        c15.append(a)
        c20.append(b)

    def resumo(xs):
        xo = sorted(xs)
        return {"media": sum(xs) / len(xs), "p95": xo[int(0.95 * len(xo))]}

    return {"n_por_bucket": n_por_bucket, "n_rodadas": n_rodadas,
            "n_pares": len(ps) * len(EIXOS),
            "esperado_acima_de_15pp_sob_o_nulo": resumo(c15),
            "esperado_acima_de_20pp_sob_o_nulo": resumo(c20)}


def _resumo_lift(lifts: list[dict]) -> dict:
    filmes = {l["slug"] for l in lifts}
    return {
        "n_pares": len(lifts),
        "n_filmes": len(filmes),
        "acima_de_15pp": sum(1 for l in lifts if l["lift"] >= 0.15),
        "acima_de_20pp": sum(1 for l in lifts if l["lift"] >= 0.20),
        "acima_de_25pp": sum(1 for l in lifts if l["lift"] >= 0.25),
        "filmes_com_ao_menos_um_15pp": len(
            {l["slug"] for l in lifts if l["lift"] >= 0.15}),
        "filmes_com_ao_menos_um_20pp": len(
            {l["slug"] for l in lifts if l["lift"] >= 0.20}),
        "por_eixo_15pp": dict(Counter(
            l["eixo"] for l in lifts if l["lift"] >= 0.15)),
        "por_bucket_vencedor_15pp": dict(Counter(
            l["bucket"] for l in lifts if l["lift"] >= 0.15)),
        "por_perfil_15pp": dict(Counter(
            l["perfil"] for l in lifts if l["lift"] >= 0.15)),
    }


def _mediana(xs: list[float]) -> float:
    xs = sorted(xs)
    n = len(xs)
    if not n:
        return 0.0
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2


def relatorio() -> dict:
    amostra = json.loads(ARQ_AMOSTRA.read_text(encoding="utf-8"))
    regs, falhas = [], []
    vistos = set()
    for linha in ARQ_CLASSIF.read_text(encoding="utf-8").splitlines():
        if not linha.strip():
            continue
        r = json.loads(linha)
        chave = (r["slug"], r["bucket"], r["id"])
        if not r.get("ok"):
            falhas.append(r)
            continue
        if chave in vistos:
            continue
        vistos.add(chave)
        regs.append(r)
    falhas = [f for f in falhas
              if (f["slug"], f["bucket"], f["id"]) not in vistos]

    perfil_de_slug = {f["slug"]: f["perfil"] for f in amostra["filmes"]}

    # --- Entrega 2: fração livre --------------------------------------------
    def so_livre(r: dict) -> bool:
        return r["eixos"] == ["livre"]

    def frac(sub: list[dict]) -> dict:
        n = len(sub)
        k = sum(1 for r in sub if so_livre(r))
        lo, hi = _wilson(k, n)
        return {"n": n, "so_livre": k, "fracao": (k / n) if n else None,
                "ic95": [lo, hi] if n else None}

    por = lambda chave: {  # noqa: E731
        v: frac([r for r in regs if chave(r) == v])
        for v in sorted({chave(r) for r in regs})}

    # MEDIÇÃO SUPLEMENTAR (etapa 2c) — `fracao_livre` descontada das reviews
    # que não dizem nada avaliável sobre o filme. NÃO substitui a métrica do
    # gate: é publicada ao lado dela, com o denominador explícito.
    ajustada = None
    if ARQ_TRIAGEM.exists():
        veredito = {}
        for linha in ARQ_TRIAGEM.read_text(encoding="utf-8").splitlines():
            if linha.strip():
                t = json.loads(linha)
                veredito[(t["slug"], t["bucket"], t["id"])] = t["veredito"]
        def sem_conteudo(r):  # noqa: E306
            return veredito.get((r["slug"], r["bucket"], r["id"])) == "sem_conteudo"

        def frac_aj(sub):  # noqa: E306
            uteis = [r for r in sub if not (so_livre(r) and sem_conteudo(r))]
            k = sum(1 for r in uteis if so_livre(r))
            lo, hi = _wilson(k, len(uteis))
            return {"n": len(uteis), "descartadas_sem_conteudo": len(sub) - len(uteis),
                    "so_livre": k, "fracao": k / len(uteis) if uteis else None,
                    "ic95": [lo, hi] if uteis else None}

        ajustada = {
            "nota": ("reviews que caíram só em `livre` E que a triagem (etapa "
                     "2c) marcou como sem conteúdo avaliável sobre o filme "
                     "saem do NUMERADOR e do DENOMINADOR — nenhum eixo novo "
                     "as recuperaria"),
            "global": frac_aj(regs),
            "por_bucket": {b: frac_aj([r for r in regs if r["bucket"] == b])
                           for b in FRONTEIRAS},
            "por_perfil": {p: frac_aj([r for r in regs
                                       if perfil_de_slug[r["slug"]] == p])
                           for p in sorted({perfil_de_slug[r["slug"]] for r in regs})},
            "por_filme": {s: frac_aj([r for r in regs if r["slug"] == s])
                          for s in sorted({r["slug"] for r in regs})},
        }

    entrega2 = {
        "global": frac(regs),
        "por_bucket": por(lambda r: r["bucket"]),
        "por_perfil": por(lambda r: perfil_de_slug[r["slug"]]),
        "por_filme": por(lambda r: r["slug"]),
        "por_filme_e_bucket": {
            f"{s}|{b}": frac([r for r in regs
                              if r["slug"] == s and r["bucket"] == b])
            for s in sorted({r["slug"] for r in regs})
            for b in FRONTEIRAS},
        "ajustada_por_triagem": ajustada,
    }

    # --- Entrega 3: temas livres --------------------------------------------
    com_livre = [r for r in regs if "livre" in r["eixos"]]
    entrega3 = {
        "n_reviews_com_livre": len(com_livre),
        "n_reviews_so_livre": sum(1 for r in regs if so_livre(r)),
        "n_ocorrencias_de_tema": sum(len(r["temas_livres"]) for r in com_livre),
        "n_rotulos_distintos": len({t for r in com_livre for t in r["temas_livres"]}),
        "familias": _familias_agregadas(
            com_livre,
            {(r["slug"], r["bucket"], r["id"]): r["texto"]
             for r in amostra["reviews"]}),
        "grupos_lexicais": _agrupar_temas(com_livre),
    }

    # --- Entrega 4: distribuição, frequência, lift ---------------------------
    n_eixos = [len([e for e in r["eixos"] if e != "livre"]) for r in regs]
    n_eixos_com_livre = [len(r["eixos"]) for r in regs]

    freq_eixo_bucket = {}
    for b in FRONTEIRAS:
        sub = [r for r in regs if r["bucket"] == b]
        freq_eixo_bucket[b] = {
            e: (sum(1 for r in sub if e in r["eixos"]) / len(sub)) if sub else None
            for e in EIXOS}
    freq_global = {e: sum(1 for r in regs if e in r["eixos"]) / len(regs)
                   for e in EIXOS}

    # lift por (filme, eixo): freq do melhor bucket menos a maior das outras
    lifts = []
    for slug in sorted({r["slug"] for r in regs}):
        porb = {b: [r for r in regs if r["slug"] == slug and r["bucket"] == b]
                for b in FRONTEIRAS}
        if any(len(v) < 3 for v in porb.values()):
            continue  # bucket pequeno demais para uma frequência significar algo
        n_min = min(len(v) for v in porb.values())
        for e in EIXOS:
            f = {b: sum(1 for r in v if e in r["eixos"]) / len(v)
                 for b, v in porb.items()}
            vencedor = max(f, key=f.get)
            outros = max(v for b, v in f.items() if b != vencedor)
            lifts.append({"slug": slug, "perfil": perfil_de_slug[slug],
                          "eixo": e, "bucket": vencedor,
                          "freq": f[vencedor], "lift": f[vencedor] - outros,
                          "n_min_bucket": n_min, "freqs": f})
    lifts.sort(key=lambda x: -x["lift"])
    # Filme com bucket pequeno produz lift ARITMETICAMENTE grande sem
    # significar nada (em n=5, uma review sozinha vale 20pp). O corte
    # `n_min_bucket >= 15` é o mesmo limiar que o piso escalonado já usa para
    # autorizar quantificador (`PISO_ESCALONADO`, estado `completa`).
    robustos = [l for l in lifts if l["n_min_bucket"] >= 15]

    entrega4 = {
        "eixos_por_review": {
            "media_sem_livre": sum(n_eixos) / len(n_eixos),
            "mediana_sem_livre": _mediana(n_eixos),
            "media_com_livre": sum(n_eixos_com_livre) / len(n_eixos_com_livre),
            "mediana_com_livre": _mediana(n_eixos_com_livre),
            "histograma": dict(sorted(Counter(n_eixos).items())),
        },
        "freq_global": freq_global,
        "freq_por_bucket": freq_eixo_bucket,
        "lift": {
            "todos_os_filmes": _resumo_lift(lifts),
            "so_buckets_com_15_ou_mais": _resumo_lift(robustos),
            "por_filme": {
                slug: {
                    "perfil": perfil_de_slug[slug],
                    "n_min_bucket": next(l["n_min_bucket"] for l in lifts
                                         if l["slug"] == slug),
                    "eixos_15pp": sum(1 for l in lifts
                                      if l["slug"] == slug and l["lift"] >= 0.15),
                    "eixos_20pp": sum(1 for l in lifts
                                      if l["slug"] == slug and l["lift"] >= 0.20),
                    "melhor_lift": max(l["lift"] for l in lifts
                                       if l["slug"] == slug),
                }
                for slug in sorted({l["slug"] for l in lifts})},
            "nulo_de_permutacao": _nulo_de_permutacao(regs),
            "nulo_parametrico_n20": _nulo_parametrico(regs, 20),
            "nulo_parametrico_n40": _nulo_parametrico(regs, 40),
            "top": lifts[:40],
            "todos": lifts,
        },
    }

    # --- Entrega 5: custo ----------------------------------------------------
    uso = Counter()
    for r in regs:
        for k, v in r["uso"].items():
            uso[k] += v
    preco = lambda u: (u["cache_miss_tokens"] * PRECO_ENTRADA_MISS  # noqa: E731
                       + u["cache_hit_tokens"] * PRECO_ENTRADA_HIT
                       + u["completion_tokens"] * PRECO_SAIDA)
    custo = preco(uso)
    custo_familias = 0.0
    if ARQ_FAMILIAS.exists():
        custo_familias = preco(json.loads(
            ARQ_FAMILIAS.read_text(encoding="utf-8"))["uso_tokens"])
    custo_triagem = 0.0
    if ARQ_TRIAGEM.exists():
        u = Counter()
        for linha in ARQ_TRIAGEM.read_text(encoding="utf-8").splitlines():
            if linha.strip():
                for k, v in json.loads(linha)["uso"].items():
                    u[k] += v
        custo_triagem = preco(u)
    n_catalogo = len([d for d in (RAIZ / "dados" / "bruto").iterdir()
                      if (d / "meta.json").exists()])
    entrega5 = {
        "modelo": MODELO,
        "n_classificadas": len(regs),
        "uso_tokens": dict(uso),
        "custo_usd_classificacao": custo,
        "custo_usd_familias_entrega3": custo_familias,
        "custo_usd_triagem_suplementar": custo_triagem,
        "custo_usd_total_do_gate": custo + custo_familias + custo_triagem,
        "custo_usd_por_review": custo / len(regs),
        "extrapolacao": {
            "n_filmes_catalogo": n_catalogo,
            "reviews_por_filme_teto": 3 * 40,
            "n_reviews_teto": n_catalogo * 3 * 40,
            "custo_usd_teto": custo / len(regs) * n_catalogo * 3 * 40,
            "nota": ("extrapolação LINEAR no nº de reviews. É conservadora "
                     "por cima: o prompt de sistema é idêntico em toda "
                     "chamada, então a fração de tokens de entrada servida "
                     "por cache só cresce com o volume."),
        },
    }

    rel = {
        "amostra": {
            "semente": amostra["semente"],
            "criterio_filmes": amostra["criterio_filmes"],
            "criterio_reviews": amostra["criterio_reviews"],
            "filmes": amostra["filmes"],
            "n_reviews_amostradas": len(amostra["reviews"]),
            "n_classificadas_ok": len(regs),
            "n_falhas": len(falhas),
        },
        "taxonomia": list(EIXOS),
        "entrega2_fracao_livre": entrega2,
        "entrega3_temas_livres": entrega3,
        "entrega4_distribuicao_e_lift": entrega4,
        "entrega5_custo": entrega5,
        "eixos_invalidos_emitidos": dict(Counter(
            e for r in regs for e in r.get("eixos_invalidos", []))),
    }
    return rel


def _cli() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("etapa", choices=["amostra", "classificar", "familias",
                                      "triagem", "relatorio"])
    ap.add_argument("--limite", type=int, default=None)
    args = ap.parse_args()
    SAIDA.mkdir(parents=True, exist_ok=True)

    if args.etapa == "amostra":
        a = montar_amostra()
        ARQ_AMOSTRA.write_text(json.dumps(a, ensure_ascii=False, indent=2),
                               encoding="utf-8")
        print(f"{len(a['filmes'])} filmes · {len(a['reviews'])} reviews "
              f"→ {ARQ_AMOSTRA.relative_to(RAIZ)}")
        for f in a["filmes"]:
            b = " ".join(f"{k[:3]}={v['amostrado']}/{v['pool']}"
                         for k, v in f["por_bucket"].items())
            print(f"  {f['perfil']:10s} {f['slug']:38s} {b}")
    elif args.etapa == "classificar":
        classificar(args.limite)
    elif args.etapa == "familias":
        familias()
    elif args.etapa == "triagem":
        triagem()
    else:
        rel = relatorio()
        ARQ_RELATORIO.write_text(json.dumps(rel, ensure_ascii=False, indent=2),
                                 encoding="utf-8")
        print(json.dumps(rel["entrega2_fracao_livre"]["global"], indent=2))
        print(f"→ {ARQ_RELATORIO.relative_to(RAIZ)}")


if __name__ == "__main__":
    _cli()
