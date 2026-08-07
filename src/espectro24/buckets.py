"""[v1.9.0] Fronteiras de bucket — CONFIGURAÇÃO, não constante (SPEC §2.2).

Este módulo é a **única** fonte de verdade sobre onde ficam as fronteiras
entre `negativas`, `medianas` e `positivas`. Todo o resto do sistema — a
lista de níveis de cada bucket, os intervalos escritos nos prompts, a
agregação do histograma, a alocação por nível, a seleção downstream — é
**derivado** daqui, nunca redigitado.

Por que isso é uma regra estrutural e não estilo: até a v1.8.2 a fronteira
estava embutida no material COLETADO (a coleta já separava por bucket), então
mudá-la custava recoletar tudo. A v1.9.0 tira a fronteira da coleta e a
transforma em parâmetro de análise; se ela voltar a aparecer hardcoded em
qualquer ponto do caminho, o desacoplamento se perde em silêncio. O teste que
roda o mapeamento sob fronteiras ALTERNATIVAS (`tests/test_fronteiras.py`) é
o que impede isso.

DEPENDÊNCIAS: este módulo não importa nada do pacote — em particular, não
importa `config`, que é quem importa daqui. A direção da seta é deliberada.
"""
from __future__ import annotations

# Os 10 níveis canônicos da escala do Letterboxd (meia em meia estrela).
# Não é configuração: é o domínio do dado de origem (§2.1).
NIVEIS: tuple[float, ...] = (0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0)

# --- Configurações de fronteira conhecidas ---------------------------------
# Formato: {nome_do_bucket: (nivel_minimo, nivel_maximo)}, ambos INCLUSIVOS.
# A ordem das chaves é a ordem de apresentação (negativas → medianas →
# positivas), preservada por dict ordenado — o render nunca reordena por peso
# (§E.4).

# OPÇÃO C (v1.9.0, EM VIGOR). Semântica: não recomendam / mornos / recomendam.
# Duas mudanças em relação à v1.8.2: 2,5★ sai de negativas e entra em mornos
# (é o ponto médio exato da escala, e lê-lo como "não recomenda" é escolha, não
# dado); 3,5★ sai de mornos e entra em positivas (na prática observada é uma
# nota de recomendação com ressalva).
FRONTEIRAS_C: dict[str, tuple[float, float]] = {
    "negativas": (0.5, 2.0),
    "medianas": (2.5, 3.0),
    "positivas": (3.5, 5.0),
}

# Fronteiras HISTÓRICAS (v1.0.0 … v1.8.2). Mantidas como configuração de
# primeira classe, não como comentário: a telemetria da v1.9.0 publica os
# shares sob as duas lado a lado, e a reversão precisa ser um valor que já
# existe, não um valor a redigitar.
FRONTEIRAS_V18: dict[str, tuple[float, float]] = {
    "negativas": (0.5, 2.5),
    "medianas": (3.0, 3.5),
    "positivas": (4.0, 5.0),
}

# A configuração EM VIGOR. Trocar esta linha (e re-rodar a seleção downstream,
# sem nenhuma requisição de rede) é o custo total de mudar de fronteira.
FRONTEIRAS: dict[str, tuple[float, float]] = FRONTEIRAS_C


def validar_fronteiras(fronteiras: dict[str, tuple[float, float]]) -> None:
    """Confere que as fronteiras PARTICIONAM os 10 níveis canônicos.

    Levanta `ValueError` com a causa exata em quatro condições: intervalo
    invertido, bucket que não contém nenhum nível canônico, nível coberto por
    mais de um bucket, e nível não coberto por nenhum. Um buraco ou uma
    sobreposição não é um detalhe estético — perderia (ou contaria em dobro)
    reviews reais no denominador do histograma, em silêncio.
    """
    for nome, faixa in fronteiras.items():
        lo, hi = faixa
        if lo > hi:
            raise ValueError(f"bucket {nome!r}: intervalo invertido ({lo} > {hi})")
        if not [n for n in NIVEIS if lo <= n <= hi]:
            raise ValueError(
                f"bucket {nome!r}: vazio — nenhum nível canônico em [{lo}, {hi}]")

    dono: dict[float, list[str]] = {n: [] for n in NIVEIS}
    for nome, (lo, hi) in fronteiras.items():
        for n in NIVEIS:
            if lo <= n <= hi:
                dono[n].append(nome)

    duplicados = {n: ds for n, ds in dono.items() if len(ds) > 1}
    if duplicados:
        detalhe = ", ".join(f"{n}★→{ds}" for n, ds in sorted(duplicados.items()))
        raise ValueError(f"níveis em mais de um bucket: {detalhe}")

    orfaos = sorted(n for n, ds in dono.items() if not ds)
    if orfaos:
        raise ValueError(f"níveis não cobertos por nenhum bucket: {orfaos}")


def mapa_de_niveis(
    fronteiras: dict[str, tuple[float, float]] | None = None,
) -> dict[str, list[float]]:
    """{bucket: [níveis]} derivado das fronteiras. Nunca escrito à mão."""
    fr = FRONTEIRAS if fronteiras is None else fronteiras
    return {nome: [n for n in NIVEIS if lo <= n <= hi]
            for nome, (lo, hi) in fr.items()}


def niveis_de(nome: str,
              fronteiras: dict[str, tuple[float, float]] | None = None
              ) -> list[float]:
    fr = FRONTEIRAS if fronteiras is None else fronteiras
    lo, hi = fr[nome]
    return [n for n in NIVEIS if lo <= n <= hi]


def bucket_de_nivel(nivel: float,
                    fronteiras: dict[str, tuple[float, float]] | None = None
                    ) -> str | None:
    """Mapeamento nível→bucket — a função pura de que fala §2.2.

    `None` para qualquer valor que não seja um dos 10 níveis canônicos (0.0,
    5.5, 2.2): um valor fora da escala não pertence a bucket nenhum, e
    devolver um bucket por proximidade esconderia um erro de parsing.
    """
    if nivel not in NIVEIS:
        return None
    fr = FRONTEIRAS if fronteiras is None else fronteiras
    for nome, (lo, hi) in fr.items():
        if lo <= nivel <= hi:
            return nome
    return None


def intervalo_de(nome: str,
                 fronteiras: dict[str, tuple[float, float]] | None = None
                 ) -> tuple[float, float]:
    fr = FRONTEIRAS if fronteiras is None else fronteiras
    return fr[nome]


def shares_por_bucket(
    por_nivel: dict[float, int],
    fronteiras: dict[str, tuple[float, float]] | None = None,
) -> dict[str, int] | None:
    """Share real (%) por bucket a partir do histograma de NOTAS.

    `None` quando não há nota alguma — sem denominador não existe share, e é
    preferível cair no fallback (§D2) a exibir 0%/0%/0%.

    ARREDONDAMENTO (invariante da v1.4.0, preservada): cada bucket é
    arredondado INDEPENDENTEMENTE, para que o número de cada grupo seja a
    melhor aproximação inteira do SEU share. Consequência aceita e
    documentada: a soma dos três pode dar 99 ou 101 (`cure` sob as fronteiras
    históricas: 3+17+79=99). Preferido a redistribuir o resto, que tornaria
    algum bucket menos fiel ao próprio dado. A interface nunca exibe a soma.

    Aceitar `fronteiras` como parâmetro é o que permite publicar os shares sob
    as fronteiras antiga e nova lado a lado (§2.2) sem duplicar a fórmula.
    """
    fr = FRONTEIRAS if fronteiras is None else fronteiras
    total = sum(por_nivel.values())
    if total <= 0:
        return None
    return {
        nome: round(100 * sum(por_nivel.get(n, 0) for n in niveis) / total)
        for nome, niveis in mapa_de_niveis(fr).items()
    }


# Falha no import se a configuração em vigor não particionar a escala — um
# erro de configuração deve aparecer na primeira linha executada, não no meio
# de uma coleta de 40 requisições.
validar_fronteiras(FRONTEIRAS)
