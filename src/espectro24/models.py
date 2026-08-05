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
    # `EDITOR_LIMIAR_FRASE_SEM_ORIGEM` (config.py). Lista vazia é o caso
    # normal — toda frase do editado rastreia até alguma frase do bruto.
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
        """
        from .config import BUCKETS

        total = sum(por_nivel.values())
        if total <= 0:
            return None
        por_bucket = {
            nome: round(100 * sum(por_nivel.get(n, 0) for n in niveis) / total)
            for nome, niveis in BUCKETS.items()
        }
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
