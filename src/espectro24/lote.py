"""[v1.9.3] Harness de LOTE — SPEC §3[H].

Orquestra [A]→[B'] (só COLETA, sem síntese) sobre uma LISTA de filmes, com
checkpoint em arquivo (resume), validação de slug barata, e falha isolada
por filme. Não modifica nenhum comportamento da camada de coleta — só
executa o pipeline já existente (`pipeline.run_pipeline`) repetidamente.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from .config import (
    COTA_POR_BUCKET,
    DADOS_BRUTO_DIR,
    ORCAMENTO_PAGINAS_POR_BUCKET,
    ORDENACAO,
)
from .fetcher import AntiBotError, FetchError, Fetcher
from .pipeline import run_pipeline
from .urls import film_page_cache_key, film_page_url

# Tolerante a singular/plural ("1 review" / "N reviews") — mesmo padrão já
# usado nos scripts de medição das sessões B/C, agora com o "s" opcional.
_REVIEWS_RE = re.compile(r'js-route-reviews.*?title="([\d,]+)&nbsp;reviews?"',
                         re.S)


def ler_lista_slugs(caminho: str | Path) -> list[str]:
    """Um slug por linha; tudo depois de `#` é comentário (linha inteira ou
    sufixo); linhas em branco são ignoradas."""
    slugs = []
    for linha in Path(caminho).read_text(encoding="utf-8").splitlines():
        sem_comentario = linha.split("#", 1)[0].strip()
        if sem_comentario:
            slugs.append(sem_comentario)
    return slugs


def validar_slug(fetcher, slug: str) -> tuple[bool, str]:
    """[§3[H]] Verificação BARATA — 1 requisição — antes de gastar orçamento
    de páginas: o slug existe e tem pelo menos 1 review.

    `histograma` ausente NÃO é checado aqui — o pipeline já degrada esse
    caso graciosamente (alocação uniforme, §3[G]); checá-lo de novo seria
    custo redundante, não segurança adicional.

    Devolve `(ok, motivo)` — `motivo == ""` quando `ok` é `True`.
    """
    try:
        html = fetcher.get(film_page_url(slug), film_page_cache_key(slug))
    except (FetchError, AntiBotError) as e:
        return False, f"slug_invalido: {e}"
    m = _REVIEWS_RE.search(html)
    n_reviews = int(m.group(1).replace(",", "")) if m else 0
    if n_reviews <= 0:
        return False, "sem_reviews"
    return True, ""


@dataclass
class ResultadoFilme:
    """Resultado de coletar UM filme — sucesso ou falha isolada."""
    slug: str
    status: str                              # "concluido" | "falhou"
    motivo: str = ""
    buckets: list = field(default_factory=list)
    superset: object = None
    distrib: object = None
    n_por_bucket: dict = field(default_factory=dict)
    estado_piso: dict = field(default_factory=dict)
    requisicoes: int = 0


def coletar_um_filme(fetcher, slug: str,
                     dados_dir: str | Path = DADOS_BRUTO_DIR,
                     cota_por_bucket: int = COTA_POR_BUCKET,
                     orcamento_paginas_bucket: int = ORCAMENTO_PAGINAS_POR_BUCKET,
                     ordenacao: str = ORDENACAO,
                     on_level=None) -> ResultadoFilme:
    """Coleta [A]→[B'] de UM filme — só coleta, `synth=False` sempre (o
    harness de lote é sobre a camada de coleta, §3[H]; síntese é decisão de
    outra sessão).

    **Falha isolada:** qualquer exceção durante a coleta deste filme vira
    `ResultadoFilme(status="falhou", motivo=...)` — nunca propaga, EXCETO
    `AntiBotError`, que é a única condição que ainda para o lote inteiro
    (mesma política do CLI de um filme só, §restrições) e por isso não é
    capturada aqui — quem chama (`rodar_lote`) decide o que fazer com ela.

    `material_esgotado` (§3[B]) não é uma falha: um filme obscuro esgotando
    material antes do orçamento produz `status="concluido"` normalmente,
    com buckets possivelmente abaixo de `completa` — resultado honesto, não
    erro do harness.
    """
    try:
        buckets, superset, distrib = run_pipeline(
            fetcher, slug, data_coleta=datetime.now(timezone.utc).isoformat(),
            synth=False, cota_por_bucket=cota_por_bucket,
            orcamento_paginas_bucket=orcamento_paginas_bucket,
            ordenacao=ordenacao, dados_dir=dados_dir, on_level=on_level,
        )
    except AntiBotError:
        raise
    except Exception as e:   # noqa: BLE001 — falha isolada é o contrato desta função
        return ResultadoFilme(slug=slug, status="falhou",
                              motivo=f"{type(e).__name__}: {e}")

    return ResultadoFilme(
        slug=slug, status="concluido", buckets=buckets, superset=superset,
        distrib=distrib,
        n_por_bucket={b.nome: b.n_validas for b in buckets},
        estado_piso={b.nome: b.estado_piso for b in buckets},
        requisicoes=getattr(fetcher, "n_network", 0),
    )


class EstadoLote:
    """[§3[H]] Checkpoint do lote — arquivo, não memória.

    Grava, por slug, `status` (`pendente`/`concluido`/`falhou`), motivo (se
    falhou) e um resumo (se concluído). `salvar()` reescreve o arquivo
    inteiro a cada chamada — deliberado: `rodar_lote` chama `salvar()` após
    CADA filme, não em lote ao final, para que uma interrupção a qualquer
    momento deixe o progresso já feito gravado.
    """

    def __init__(self, caminho: str | Path):
        self.caminho = Path(caminho)
        self._dados: dict = {"slugs": {}}

    def carregar(self) -> "EstadoLote":
        if self.caminho.exists():
            self._dados = json.loads(self.caminho.read_text(encoding="utf-8"))
            self._dados.setdefault("slugs", {})
        return self

    def status(self, slug: str) -> str:
        return self._dados["slugs"].get(slug, {}).get("status", "pendente")

    def dados(self, slug: str) -> dict:
        return self._dados["slugs"].get(slug, {})

    def marcar_concluido(self, slug: str, n_por_bucket: dict, requisicoes: int,
                         estado_piso: dict | None = None) -> None:
        self._dados["slugs"][slug] = {
            "status": "concluido",
            "atualizado_em": datetime.now(timezone.utc).isoformat(),
            "n_por_bucket": n_por_bucket,
            "estado_piso": estado_piso or {},
            "requisicoes": requisicoes,
        }

    def marcar_falhou(self, slug: str, motivo: str) -> None:
        self._dados["slugs"][slug] = {
            "status": "falhou",
            "atualizado_em": datetime.now(timezone.utc).isoformat(),
            "motivo": motivo,
        }

    def salvar(self) -> None:
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        self.caminho.write_text(
            json.dumps(self._dados, ensure_ascii=False, indent=2), encoding="utf-8")


@dataclass
class RelatorioLote:
    """Agregado de uma execução (ou retomada) de `rodar_lote`."""
    n_concluidos: int = 0
    n_pulados: int = 0
    n_falhas: int = 0
    falhas: dict = field(default_factory=dict)     # slug -> motivo
    resultados: list = field(default_factory=list)  # ResultadoFilme dos processados


def rodar_lote(slugs: list[str], *,
               cache_dir: str = "resultado/cache",
               dados_dir: str | Path = DADOS_BRUTO_DIR,
               estado_path: str | Path,
               cota_por_bucket: int = COTA_POR_BUCKET,
               orcamento_paginas_bucket: int = ORCAMENTO_PAGINAS_POR_BUCKET,
               ordenacao: str = ORDENACAO,
               fabrica_fetcher=None,
               on_progress=None) -> RelatorioLote:
    """[§3[H]] Roda a coleta de `slugs`, um a um, com checkpoint/resume.

    `fabrica_fetcher(slug) -> fetcher`: por padrão cria um `Fetcher` real
    por filme (mesmo padrão do CLI de um filme só); testável injetando uma
    fábrica que devolve `FakeFetcher`.

    `on_progress(slug, status, motivo)`: chamado depois de cada slug
    processado (`status` em `pulado`/`concluido`/`falhou`) — log por filme
    (§3[H]); sem isso um lote de horas fica indistinguível de travado.

    Slug já `concluido` no checkpoint é PULADO sem gastar nenhuma
    requisição — essa é a garantia de resume.
    """
    fabrica_fetcher = fabrica_fetcher or (lambda slug: Fetcher(cache_dir=cache_dir))
    estado = EstadoLote(estado_path).carregar()
    rel = RelatorioLote()

    for slug in slugs:
        if estado.status(slug) == "concluido":
            rel.n_pulados += 1
            if on_progress:
                on_progress(slug, "pulado", None)
            continue

        fetcher = fabrica_fetcher(slug)
        ok, motivo = validar_slug(fetcher, slug)
        if not ok:
            estado.marcar_falhou(slug, motivo)
            estado.salvar()
            rel.falhas[slug] = motivo
            rel.n_falhas += 1
            if on_progress:
                on_progress(slug, "falhou", motivo)
            continue

        try:
            resultado = coletar_um_filme(
                fetcher, slug, dados_dir=dados_dir, cota_por_bucket=cota_por_bucket,
                orcamento_paginas_bucket=orcamento_paginas_bucket, ordenacao=ordenacao)
        except AntiBotError as e:
            # Única exceção que ainda para o lote inteiro (§restrições) —
            # mas registrada no checkpoint ANTES de propagar, para o resume
            # saber exatamente onde parou.
            estado.marcar_falhou(slug, f"anti_bot: {e}")
            estado.salvar()
            raise

        if resultado.status == "falhou":
            estado.marcar_falhou(slug, resultado.motivo)
            rel.falhas[slug] = resultado.motivo
            rel.n_falhas += 1
        else:
            estado.marcar_concluido(slug, n_por_bucket=resultado.n_por_bucket,
                                    requisicoes=resultado.requisicoes,
                                    estado_piso=resultado.estado_piso)
            rel.n_concluidos += 1
        estado.salvar()
        rel.resultados.append(resultado)
        if on_progress:
            on_progress(slug, resultado.status, resultado.motivo or None)

    return rel
