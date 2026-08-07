"""[v1.9.0] Persistência do superset bruto — SPEC §3[B'].

Este módulo guarda o artefato que **desacopla coleta de análise**: reviews
etiquetadas por **nível de estrela** (dado do Letterboxd) e nada mais. Ele não
sabe onde ficam as fronteiras de bucket, qual é a cota, qual filtro de
comprimento vale, nem o que é spoiler-excluído — todas essas são decisões de
análise, aplicadas depois, sobre este material (§3[C2]).

Layout:

    dados/bruto/<slug>/meta.json
    dados/bruto/<slug>/reviews.jsonl

**Versionado no git**, ao contrário de `resultado/cache/` (que é
`.gitignore`d): o cache é HTML reconstruível e volumoso; o bruto é o insumo
de análise — pequeno, textual, e exatamente a coisa cuja recoleta a v1.9.0
existe para evitar.

Três propriedades das quais o desacoplamento depende, todas testadas em
`tests/test_bruto.py`:

- **idempotente** — persistir o mesmo material duas vezes produz o mesmo
  arquivo, byte a byte;
- **dedupe por `id`** — recoletar um filme já coletado não duplica review;
- **incremental** — coletas sucessivas ACUMULAM superset (trocar a ordenação
  e recoletar soma material em vez de substituí-lo).
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from .config import DADOS_BRUTO_DIR


@dataclass(frozen=True)
class ReviewBruta:
    """Uma review como ela foi RASPADA — nenhuma decisão de análise embutida.

    Os oito primeiros campos são o formato de §3[B']. Os três últimos são
    adições documentadas na mesma seção; todas são **propriedades da review**,
    nunca decisões de seleção, e por isso respeitam o mesmo princípio que
    mantém `passou_por_relaxamento` fora daqui:

    - `truncada` — veio colapsada na listagem (detector `.collapsed-text`).
      Sem ela, a invariante de v1.1.0 "texto truncado nunca chega ao LLM"
      seria impossível de garantir a partir do bruto: `n_chars` de um texto
      cortado não distingue "review curta" de "review longa truncada".
    - `texto_completo` — `texto` é o texto integral (nunca foi truncada, ou o
      completamento [C'] resolveu). A seleção só considera elegível quem tem
      `True` aqui.
    - `data` — a data da review. É a EVIDÊNCIA de que `ordenacao_usada` é o
      que se declara; sem ela, a ordenação gravada no meta seria uma
      afirmação inverificável a partir do próprio material coletado.
    """
    id: str
    nivel: float
    texto: str
    n_chars: int
    spoiler_flag: bool
    pagina_origem: int
    url: str
    autor_hash: str
    truncada: bool
    texto_completo: bool
    data: str | None

    def para_review(self):
        """Adaptador para a `Review` que a camada de análise (§D) consome.

        `full_text` recebe o texto persistido porque, para uma review que
        chegou aqui, ele JÁ é o texto vigente — a seleção só considera
        elegível quem tem `texto_completo`. Assim `effective_text` (que o
        prompt da síntese usa) devolve o texto certo sem caso especial.
        `rating` vem do `nivel`, que veio da URL de coleta (autoritativa).
        """
        from .models import Review

        return Review(
            viewing_id=self.id, rating=self.nivel, text=self.texto,
            truncated=self.truncada, full_text_url=None,
            spoiler=self.spoiler_flag, full_text=self.texto,
            permalink=self.url or None, data=self.data,
        )


@dataclass
class ResultadoPersistencia:
    """Telemetria de uma escrita — o que era novo, o que foi atualizado."""
    n_novas: int
    n_atualizadas: int
    n_total: int


def autor_hash(autor: str | None) -> str:
    """Hash estável do handle do autor.

    ESTÁVEL entre execuções e entre filmes (sem sal), para que dois registros
    do mesmo autor sejam reconhecíveis como tal — útil para medir diversidade
    de amostra. Guardar o hash em vez do handle é o mínimo de higiene: o
    handle é público, mas não há razão para o artefato de análise carregar
    identificadores de pessoas em claro.
    """
    if not autor:
        return ""
    return hashlib.blake2s(autor.encode("utf-8"), digest_size=8).hexdigest()


def id_estavel(nivel: float, texto: str) -> str:
    """Id derivado do CONTEÚDO, para review sem `viewing_id` do Letterboxd.

    Sem um id, o dedupe cairia e cada recoleta duplicaria essas reviews — a
    incrementalidade morreria em silêncio justamente no material mais frágil.
    Derivar de `(nivel, texto)` é determinístico, então a mesma review anônima
    vinda duas vezes continua sendo uma só. Prefixo `txt:` deixa explícito, ao
    ler o arquivo, que aquele id não é do Letterboxd.
    """
    h = hashlib.blake2s(f"{nivel}|{texto}".encode("utf-8"), digest_size=10)
    return f"txt:{h.hexdigest()}"


def dir_do_filme(slug: str, raiz: str | Path = DADOS_BRUTO_DIR) -> Path:
    return Path(raiz) / slug


def caminho_meta(slug: str, raiz: str | Path = DADOS_BRUTO_DIR) -> Path:
    return dir_do_filme(slug, raiz) / "meta.json"


def caminho_reviews(slug: str, raiz: str | Path = DADOS_BRUTO_DIR) -> Path:
    return dir_do_filme(slug, raiz) / "reviews.jsonl"


def carregar(slug: str, raiz: str | Path = DADOS_BRUTO_DIR
             ) -> tuple[dict | None, list[ReviewBruta]]:
    """Lê `(meta, reviews)` do disco. Filme nunca coletado → `(None, [])`.

    Linha corrompida (JSON inválido ou campo faltando) é **ignorada**, não
    derruba a carga: o bruto é um append-log e uma escrita interrompida no
    meio de uma linha não pode invalidar as milhares de linhas boas antes
    dela. Perder uma review é degradação aceitável; perder o arquivo não é.
    """
    meta = None
    p_meta = caminho_meta(slug, raiz)
    if p_meta.exists():
        try:
            meta = json.loads(p_meta.read_text(encoding="utf-8"))
        except ValueError:
            meta = None

    reviews: list[ReviewBruta] = []
    p_rev = caminho_reviews(slug, raiz)
    if p_rev.exists():
        for linha in p_rev.read_text(encoding="utf-8").splitlines():
            if not linha.strip():
                continue
            try:
                reviews.append(ReviewBruta(**json.loads(linha)))
            except (ValueError, TypeError):
                continue
    return meta, reviews


def percentil(valores_ordenados: list, p: float):
    """Percentil `p` (0-1) por nearest-rank sobre uma sequência JÁ ordenada.

    Genérico — funciona sobre datas (`janela_temporal`) e sobre inteiros de
    `pagina_origem` (`distribuicao_pagina_origem`, v1.9.2): uma única fórmula
    de percentil, não duas.

    `n == 1` devolve o único valor para qualquer `p` — não há o que
    interpolar. Índice sempre clampado a `[0, n-1]`.
    """
    n = len(valores_ordenados)
    if n == 1:
        return valores_ordenados[0]
    idx = max(0, min(n - 1, round(p * (n - 1))))
    return valores_ordenados[idx]


def janela_temporal(reviews: Iterable[ReviewBruta]) -> dict | None:
    """[v1.9.1, §3[B']] min/max/p5/p50/p95 das datas de uma lista de reviews.

    **Função pura e bucket-agnóstica** — opera sobre QUALQUER lista que
    receba, sem embutir fronteira nenhuma; quem agrupa por bucket antes de
    chamar é `pipeline.py` (§3[B'], "Janela temporal").

    Motivada por dois achados: o viés de recência medido na v1.9.0 e o
    achado do gate de profundidade desta versão de que `min`/`max` sozinhos
    são enganosos — `data` é a data ASSISTIDA (diário), não a de publicação,
    e um único outlier em qualquer posição da amostra domina o extremo. A
    mediana (`p50`) é a leitura honesta de "quando a amostra realmente está".

    Datas truncadas para `YYYY-MM-DD` (o campo `data` mistura formatos com e
    sem hora — a hora não importa para janela). `None` quando não há
    nenhuma review com `data`.
    """
    datas = sorted((r.data or "")[:10] for r in reviews if r.data)
    if not datas:
        return None
    return {
        "n": len(datas),
        "min": datas[0],
        "max": datas[-1],
        "p5": percentil(datas, 0.05),
        "p50": percentil(datas, 0.50),
        "p95": percentil(datas, 0.95),
    }


def distribuicao_pagina_origem(
    reviews: Iterable[ReviewBruta],
    orcamento_por_nivel: dict[float, int] | None = None,
) -> dict | None:
    """[v1.9.2, §3[B']] min/max/p5/p50/p95 de `pagina_origem` — instrumento
    temporal PRIMÁRIO, sobre a amostra SELECIONADA (quem chama decide o quê:
    normalmente `pipeline.py` passa só as reviews escolhidas de um bucket,
    não o bruto inteiro).

    Substitui `janela_temporal` (por `data`) como sinal principal de "onde a
    amostra está": `data` é a data ASSISTIDA, contaminada por quem registra
    filmes com atraso (causa do resultado misto do gate de profundidade,
    v1.9.1). `pagina_origem`, sob ordenação cronológica, é o RANK DE ADIÇÃO
    — sem essa contaminação.

    `fracao_profunda`: fração da amostra cujo `pagina_origem` cai no bloco
    PROFUNDO do respectivo nível (posicionamento estratificado, §3[B]) —
    calculada com a MESMA `alocacao.dividir_raso_profundo` usada na coleta,
    para que telemetria e coleta nunca divirjam sobre o que conta como
    "profundo". `None` quando `orcamento_por_nivel` não é fornecido (não dá
    para saber onde fica o corte raso/profundo sem o orçamento que gerou a
    amostra).

    Função pura e bucket-agnóstica, como `janela_temporal`. `None` quando a
    lista está vazia.
    """
    from .alocacao import dividir_raso_profundo

    reviews = list(reviews)
    paginas = sorted(r.pagina_origem for r in reviews)
    if not paginas:
        return None

    fracao_profunda = None
    if orcamento_por_nivel is not None:
        n_raso_por_nivel: dict[float, int] = {}
        n_profundas = 0
        for r in reviews:
            orc = orcamento_por_nivel.get(r.nivel)
            if orc is None:
                continue
            if r.nivel not in n_raso_por_nivel:
                n_raso_por_nivel[r.nivel], _ = dividir_raso_profundo(orc)
            if r.pagina_origem > n_raso_por_nivel[r.nivel]:
                n_profundas += 1
        fracao_profunda = n_profundas / len(reviews)

    return {
        "n": len(paginas),
        "min": paginas[0],
        "max": paginas[-1],
        "p5": percentil(paginas, 0.05),
        "p50": percentil(paginas, 0.50),
        "p95": percentil(paginas, 0.95),
        "fracao_profunda": fracao_profunda,
    }


def atualizar_meta(slug: str, atualizacoes: dict,
                   raiz: str | Path = DADOS_BRUTO_DIR) -> None:
    """Mescla `atualizacoes` no `meta.json` existente — NÃO toca `reviews.jsonl`.

    Usado por `pipeline.py` para gravar `janela_temporal` (§3[B'], bucket-aware)
    como um passo posterior a `persistir()` (bucket-agnóstico), sem reescrever
    o log de reviews. Filme sem `meta.json` ainda cria um novo com só as
    `atualizacoes` — não é o caminho normal (toda coleta passa por
    `persistir()` primeiro), mas não quebra.
    """
    meta, _ = carregar(slug, raiz=raiz)
    meta = dict(meta) if meta else {}
    meta.update(atualizacoes)
    destino = dir_do_filme(slug, raiz)
    destino.mkdir(parents=True, exist_ok=True)
    caminho_meta(slug, raiz).write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def persistir(slug: str, meta: dict, reviews: Iterable[ReviewBruta],
              raiz: str | Path = DADOS_BRUTO_DIR) -> ResultadoPersistencia:
    """Grava o lote, mesclando com o que já existe. Idempotente e incremental.

    Semântica do merge, por `id`:
    - id novo → **anexa** ao fim (preserva a ordem de amostragem);
    - id já presente → **sobrescreve na posição original**. Isso é o que
      permite um completamento resolvido numa execução POSTERIOR entrar sem
      embaralhar a ordem de que a seleção depende (§3[C2], passo 5): a review
      persistida truncada numa coleta ganha o texto completo na seguinte, no
      mesmo lugar.

    `meta` é **sobrescrito** pela execução mais recente, enquanto as reviews
    ACUMULAM — a assimetria é deliberada: o meta descreve a última coleta, o
    jsonl descreve todo o material já visto.

    Lote vazio não apaga nada (é o caso de uma recoleta 100% em cache).
    """
    _, existentes = carregar(slug, raiz)
    por_id: dict[str, ReviewBruta] = {r.id: r for r in existentes}
    ordem: list[str] = list(por_id)

    n_novas = n_atualizadas = 0
    vistos_no_lote: set[str] = set()
    for r in reviews:
        if r.id in por_id:
            # Só conta como atualização se algo realmente mudou — assim
            # `persistir` do mesmo material duas vezes reporta 0/0, que é a
            # leitura honesta de "nada aconteceu".
            if por_id[r.id] != r and r.id not in vistos_no_lote:
                n_atualizadas += 1
            por_id[r.id] = r
        else:
            por_id[r.id] = r
            ordem.append(r.id)
            n_novas += 1
        vistos_no_lote.add(r.id)

    destino = dir_do_filme(slug, raiz)
    destino.mkdir(parents=True, exist_ok=True)
    caminho_reviews(slug, raiz).write_text(
        "".join(json.dumps(asdict(por_id[i]), ensure_ascii=False) + "\n"
                for i in ordem),
        encoding="utf-8")
    caminho_meta(slug, raiz).write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return ResultadoPersistencia(n_novas=n_novas, n_atualizadas=n_atualizadas,
                                 n_total=len(ordem))
