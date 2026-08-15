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
    # v1.9.0 (§3[B']): metadados persistidos no superset bruto. `autor` é o
    # handle público (guardado só em memória — o que vai para o disco é o
    # `autor_hash`); `permalink` é a URL da review; `data` é a data em que
    # ela foi escrita, que é a EVIDÊNCIA de que a ordenação declarada em
    # `meta.json` é a que de fato foi usada (§2.3).
    autor: str | None = None
    permalink: str | None = None
    data: str | None = None

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
    # v1.9.0: a alocação de §3[C1] para este nível — é o "ALVO" da ressalva 2
    # (a redistribuição de déficit muda a composição em silêncio). Sem ele, a
    # composição ATINGIDA não é interpretável: 40 alcançados como planejado e
    # 40 alcançados por redistribuição não podem parecer a mesma coisa.
    n_alvo: int = 0
    # v1.9.0: persistidas no bruto mas inelegíveis por texto incompleto
    # (truncada cujo completamento não foi feito ou falhou). Torna visível o
    # material que existe mas a regra "nunca pela metade" mantém de fora.
    n_indisponivel_truncamento: int = 0
    # v1.9.1 (§3[C2]): motivo→n, cada review do bruto classificada em
    # exatamente uma categoria. `n_descartadas_spoiler`/`n_descartadas_curtas`/
    # `n_indisponivel_truncamento` acima são DERIVADOS deste dict — uma
    # fonte de verdade, não duas contagens que podem divergir.
    motivos_descarte: dict = field(default_factory=dict)

    @property
    def n_validas(self) -> int:
        return len(self.validas)

    def metadata(self) -> dict[str, Any]:
        return {
            "nivel": self.nivel,
            "n_validas": self.n_validas,
            "n_alvo": self.n_alvo,
            "n_brutas": self.n_brutas,
            "filtro_aplicado": self.filtro_aplicado,
            "n_sem_nota": self.n_sem_nota,
            "n_descartadas_spoiler": self.n_descartadas_spoiler,
            "n_descartadas_curtas": self.n_descartadas_curtas,
            "n_descartadas_truncamento": self.n_descartadas_truncamento,
            "n_indisponivel_truncamento": self.n_indisponivel_truncamento,
            "motivos_descarte": self.motivos_descarte,
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
    # v1.4.1: a MESMA flag passa a ser alimentada também pela checagem POR PAR
    # de `quantificadores_usados` (quantificador declarado mais forte que o
    # rótulo do tema declarado, ou tema inexistente) — a checagem de bucket
    # continua ativa, esta é somada a ela.
    quantificador_suspeito: bool = False
    falhou: bool = False  # True se não houve JSON válido nem após retentativa
    # v1.3.1: telemetria dos consensos factuais usados no MOVIMENTO 2 — cada
    # item é {propriedade, grupos_de_origem, temas_de_origem}, declarado pelo
    # próprio LLM para permitir revisão humana (o consenso é real ou
    # inventado?). `consenso_suspeito` = True quando algum item citou
    # grupo/tema inexistente no relatório e a retentativa não corrigiu.
    consensos_usados: list = field(default_factory=list)
    consenso_suspeito: bool = False
    # v1.4.0: True quando havia distribuição real e a prosa NÃO ancorou algum
    # grupo no rotulo_peso fornecido (nem num rótulo mais fraco, nem no
    # percentual) — isto é, o narrador ignorou o peso e tratou os grupos como
    # equivalentes — e a retentativa não corrigiu. Sempre False quando não há
    # distribuição (não há o que ancorar).
    peso_nao_ancorado: bool = False
    # v1.4.1: telemetria dos quantificadores usados no MOVIMENTO 3 — cada item
    # é {quantificador, tema}, declarado pelo próprio LLM junto do tema EXATO
    # de onde a frequência vem. Mesmo padrão de `consensos_usados` (v1.3.1):
    # material pronto para revisão humana par a par, e insumo da checagem que
    # alimenta `quantificador_suspeito`.
    quantificadores_usados: list = field(default_factory=list)
    # v1.4.1: True quando havia distribuição real e um rótulo de peso apareceu
    # acompanhado de "reviews"/"público"/"espectadores" em vez de "notas" — o
    # peso vem do histograma de NOTAS, os temas vêm das reviews com texto, e
    # os dois vocabulários não se misturam — e a retentativa não corrigiu.
    vocabulario_peso_suspeito: bool = False
    # v1.5.0: telemetria dos marcadores de perspectiva ("para eles", "nessa
    # leitura") declarados pelo narrador — cada item é {grupo, trecho}, no
    # mesmo padrão de consensos_usados/quantificadores_usados. Existe para
    # que a remoção dos verbos de reporte (regra de registro) não deixe a
    # fala de um grupo minoritário soar como fato do narrador.
    marcadores_perspectiva: list = field(default_factory=list)
    # v1.5.0: True quando algum grupo com marcação exigida (simples/antecipada,
    # pré-computada a partir do share_real) não teve marcador declarado, teve
    # um trecho que não aparece literalmente na narrativa, ou (caso
    # "antecipada") o trecho veio depois do meio do movimento — e a
    # retentativa não corrigiu. Sempre False sem distribuição (não há share
    # para calcular a marcação).
    perspectiva_nao_marcada: bool = False
    # v1.5.0: métricas de fluência calculadas em CÓDIGO sobre o texto final —
    # n_frases, media_palavras, cv_comprimento (desvio padrão / média de
    # palavras por frase), frase_mais_curta, aberturas_repetidas,
    # verbos_reporte, adverbios_mente. Ver `_metricas_fluencia` em
    # synthesize.py — mesma política de telemetria visível, não correção
    # silenciosa de estilo.
    # v1.6.0: as métricas viram DIAGNÓSTICO PURO — a flag `fluencia_baixa` e
    # os gatilhos de retentativa por métrica foram REMOVIDOS, porque as
    # métricas não acompanham qualidade (no `cure`, o texto melhor pontuou
    # pior; ver DIAGNOSTICO_FLUENCIA_V2.md e a nota em synthesize.py).
    metricas_fluencia: dict = field(default_factory=dict)


@dataclass
class NarrativaBriefingResult:
    """[v1.9.11] Saída do narrador de PRODUÇÃO (briefing + best-of-3).

    Substitui `NarrativaResult` no caminho de produção. A diferença de
    conteúdo é a diferença de ARQUITETURA entre os dois narradores: o antigo
    pedia ao LLM que DECLARASSE o que tinha feito (`consensos_usados`,
    `quantificadores_usados`, `marcadores_perspectiva`) e validava a
    declaração; o novo não pede declaração nenhuma — o código já decidiu
    tudo no briefing, e a verificação roda sobre o TEXTO
    (`qualidade.verificar`).

    `candidatos` guarda as N narrativas geradas (as perdedoras inclusive) —
    é o que torna a escolha auditável em memória. O que vai para o JSON de
    resultado é só a MÉTRICA de cada uma (ver `narrador.telemetria_para_json`).
    """
    texto: str                     # a narrativa ESCOLHIDA (ou "" se falhou)
    falhou: bool = False           # nenhuma das N amostras devolveu texto
    briefing: dict = field(default_factory=dict)
    candidatos: list = field(default_factory=list)
    escolha: dict | None = None    # saída de `selecao_narrativa.selecionar`
    retry: dict | None = None      # retry direcionado, quando houve
    verificacao: dict = field(default_factory=dict)  # `qualidade.verificar`
    provider: str = ""
    modelo: str = ""
    # Custo do estágio INTEIRO, não da chamada vencedora: `BEST_OF_N`
    # chamadas por filme (mais uma no pior caso, com o retry). Somar é o que
    # impede o custo real do best-of-3 de ficar invisível no JSON.
    n_chamadas: int = 0
    uso: dict = field(default_factory=dict)
    latencia_s: float = 0.0


# `EdicaoResult` (saída da etapa [E2]) foi removida daqui na v1.9.10 — o
# editor foi APOSENTADO (ver SPEC.md, "Fechamento do narrador"). A classe
# vive agora em `experimentos-editor-e2-arquivado/editor.py`, junto com o
# resto do estágio.


@dataclass
class Distribuicao:
    """[v1.4.0] Distribuição REAL de notas do filme (histograma do Letterboxd).

    Distinta da cota de coleta (50/20/30), que é amostragem estratificada e
    NÃO reflete prevalência. Este é o dado que faltava para a v1.2.1 — que
    proibiu afirmações de prevalência justamente por não tê-lo (ver SPEC
    §D2 e o changelog da v1.2.1, que já previa esta feature).

    `por_bucket` guarda o **share real** de cada faixa em percentual inteiro.
    NÃO é uma nota média nem um score agregado: são três números, um por
    perspectiva, que somam a população de notas — a proibição de score
    único (§1) permanece intacta.
    """
    por_nivel: dict[float, int]          # {0.5: 456, …, 5.0: 99242}
    n_notas_total: int
    por_bucket: dict[str, int]           # {"negativas": 3, "medianas": 17, …}
    fonte: str = "letterboxd_histograma"

    @classmethod
    def de_histograma(cls, por_nivel: dict[float, int]) -> "Distribuicao | None":
        """Agrega o histograma por bucket (§2 BUCKETS). None se não houver
        nota alguma — sem denominador não existe share, e é preferível cair
        no fallback (regras v1.2.1) a exibir 0%/0%/0%.

        ARREDONDAMENTO: cada bucket é arredondado independentemente, para
        que o número de cada grupo seja a melhor aproximação inteira do SEU
        share. Consequência aceita e documentada: a soma dos três pode dar
        99 ou 101. Preferido a redistribuir o resto (que tornaria algum
        bucket menos fiel ao próprio dado) — coerente com a política do
        projeto de não maquiar número. A interface nunca exibe a soma.

        v1.9.0: a agregação delega a `buckets.shares_por_bucket`, que aceita
        as fronteiras como PARÂMETRO — é a mesma função usada para publicar
        os shares sob as fronteiras antiga e nova lado a lado (§2.2), então
        não existe uma segunda fórmula a divergir desta.
        """
        from .buckets import shares_por_bucket

        total = sum(por_nivel.values())
        por_bucket = shares_por_bucket(por_nivel)
        if por_bucket is None:
            return None
        return cls(por_nivel=dict(por_nivel), n_notas_total=total,
                   por_bucket=por_bucket)

    def metadata(self) -> dict[str, Any]:
        return {
            "n_notas_total": self.n_notas_total,
            # chaves como string p/ o JSON não virar "0.5" vs 0.5 conforme o parser
            "por_nivel": {str(k): v for k, v in sorted(self.por_nivel.items())},
            "por_bucket": dict(self.por_bucket),
            "fonte": self.fonte,
        }


@dataclass
class BucketResult:
    nome: str
    alvo: int
    modo: str                      # completo | reduzido | sem_analise
    # v1.9.0 (§3[C3]): piso ESCALONADO — completa | sem_quantificador |
    # sem_numero | sem_analise, calculado sobre o n final. Convive com `modo`
    # em vez de substituí-lo: `modo` é consumido por render e frontend, que
    # estão fora do escopo desta versão. Nesta sessão só o CAMPO é exposto —
    # as variantes de narrador e os estados de UI ficam para depois.
    estado_piso: str = "sem_analise"
    niveis: list[LevelResult] = field(default_factory=list)
    # v1.9.0: telemetria da seleção (§4). `composicao_alvo` vs.
    # `composicao_atingida` é a mitigação OBRIGATÓRIA da ressalva 2 de
    # §3[C1] — a redistribuição de déficit muda a composição em silêncio, e
    # sem os dois lado a lado isso ficaria invisível.
    composicao_alvo: dict = field(default_factory=dict)
    composicao_atingida: dict = field(default_factory=dict)
    cascata_por_degrau: dict = field(default_factory=dict)
    deficit_redistribuido: int = 0
    # v1.9.2 (§3[B']): instrumento temporal PRIMÁRIO — distribuição de
    # `pagina_origem` (rank de adição, sem a contaminação de `data`, que é a
    # data ASSISTIDA) sobre a amostra SELECIONADA deste bucket.
    # `{n, min, max, p5, p50, p95, fracao_profunda}` ou `None`.
    distribuicao_pagina_origem: dict | None = None
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
