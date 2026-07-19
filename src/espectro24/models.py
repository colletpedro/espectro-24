"""Estruturas de dados do pipeline."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class Review:
    viewing_id: str            # ex. "viewing:412989206" (fonte de dedup/cache)
    rating: float | None       # nota em estrelas (0.5 .. 5.0) ou None
    text: str                  # texto VISÍVEL (pode estar truncado)
    truncated: bool            # detector de colapso (.collapsed-text / …)
    full_text_url: str | None  # /s/full-text/viewing:<id>/ quando disponível
    spoiler: bool              # placeholder de spoiler no corpo
    lang: str | None = None
    full_text: str | None = None  # preenchido em C' (texto completo)

    @property
    def chars(self) -> int:
        """Comprimento do texto vigente (completo se resolvido, senão visível)."""
        return len(self.effective_text)

    @property
    def effective_text(self) -> str:
        return self.full_text if self.full_text is not None else self.text


@dataclass
class SearchResult:
    slug: str
    name: str            # ex. "City of God (2002)"
    year: int | None
    link: str


@dataclass
class LevelResult:
    nivel: float
    filtro_aplicado: int              # chars do filtro que vigorou (0 = sem filtro)
    paginas_buscadas: int
    n_brutas: int
    n_sem_nota: int
    n_descartadas_spoiler: int
    n_descartadas_curtas: int
    n_descartadas_truncamento: int
    validas: list[Review] = field(default_factory=list)

    @property
    def n_validas(self) -> int:
        return len(self.validas)

    def metadata(self) -> dict[str, Any]:
        return {
            "nivel": self.nivel,
            "n_validas": self.n_validas,
            "n_brutas": self.n_brutas,
            "filtro_aplicado": self.filtro_aplicado,
            "n_sem_nota": self.n_sem_nota,
            "n_descartadas_spoiler": self.n_descartadas_spoiler,
            "n_descartadas_curtas": self.n_descartadas_curtas,
            "n_descartadas_truncamento": self.n_descartadas_truncamento,
            "paginas_buscadas": self.paginas_buscadas,
        }


@dataclass
class Tema:
    tema: str
    mencoes_aproximadas: int
    n_reviews_analisadas: int
    exemplo_parafraseado: str
    # Sinal de alucinação: True quando o LLM devolveu um numerador fora de
    # [0, n_reviews_analisadas] e o código teve que corrigi-lo (SPEC §D / v1.1.1).
    mencoes_clampadas: bool = False
    mencoes_valor_original: int | None = None  # valor cru do LLM, só se clampado
    # v1.1.2: True quando exemplo_parafraseado continha aspas de citação e o
    # código as removeu mecanicamente (violação da regra de paráfrase).
    aspas_removidas: bool = False


@dataclass
class NarrativaResult:
    """Saída da etapa [D2] (v1.2.0): prosa narrativa + telemetria das
    validações pós-parsing aplicadas sobre o texto (idioma, aspas, escopo).

    A assinatura da spec `narrate_output(...) -> str` refere-se ao campo
    `.texto`; as flags acompanham para telemetria (mesma política do §D).
    """
    texto: str
    idioma_invalido: bool = False
    escopo_suspeito: bool = False
    aspas_removidas: bool = False
    # v1.2.1: True quando a prosa comparou tamanhos entre grupos / inferiu
    # prevalência global (defeito: cota de amostragem apresentada como
    # distribuição da recepção) e a retentativa não corrigiu.
    prevalencia_suspeita: bool = False
    # v1.2.3: True quando a prosa usou "quase todos"/"praticamente todos"
    # sem que NENHUM tema do filme tivesse fração >= 80% (o único modo de
    # falha observado de quantificador mais forte que o rótulo pré-computado
    # permitia) e a retentativa não corrigiu.
    quantificador_suspeito: bool = False
    falhou: bool = False  # True se não houve JSON válido nem após retentativa


@dataclass
class BucketResult:
    nome: str
    alvo: int
    modo: str                      # completo | reduzido | sem_analise
    niveis: list[LevelResult] = field(default_factory=list)
    temas: list[Tema] = field(default_factory=list)
    observacao_geral: str = ""
    # v1.1.2: rede de segurança pós-parsing (§D) — telemetria, não correção
    # de conteúdo. True se a validação (com 1 retentativa) não conseguiu
    # corrigir o problema.
    idioma_invalido: bool = False
    escopo_suspeito: bool = False

    @property
    def reviews_analisadas(self) -> list[Review]:
        return [r for lvl in self.niveis for r in lvl.validas]

    @property
    def n_validas(self) -> int:
        return sum(lvl.n_validas for lvl in self.niveis)
