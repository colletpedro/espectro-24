"""Exceção C22 (2026-09-22): os 55 do lote noturno classificados em GEMINI.

O saldo do DeepSeek acabou com o lote de 18/09 no passe 3 (38%), e o dono não
vai recarregar. Decisão dele: estes 55 — e SÓ estes — refazem os TRÊS passes
de classificação e o verificador `V2_alvo` em Gemini. Um provider por filme:
nunca dois votos de um modelo e um de outro na mesma review, porque a votação
de 3 pressupõe três sorteios do MESMO modelo (ABERTO.md C22).

Por que um módulo com a lista, e não uma troca em `PROVIDER_POR_ESTAGIO`: a
chave `classificacao` é compartilhada com a síntese, e o `taxonomia_id` não
inclui o modelo — uma troca no config contaminaria em silêncio qualquer
execução futura. Aqui a exceção só vale para quem está na lista, e só quando
o driver a pede (`lote_em_blocos.py --excecao-gemini`).

A lista é a de `dados/lote/lista-noturno-2026-09-18.txt` (conferida: os mesmos
55, e são exatamente os filmes da amostra sem `resultado/<slug>.json`).
"""
from __future__ import annotations

# A marca gravada em TODO registro (passe e verificador) feito sob a exceção.
# É por ela — e não pelo `provider` — que o consenso reconhece o registro:
# o fallback de conteúdo (C16) também grava `provider: gemini`, e aquele é
# outro regime (troca pontual, dentro de filme DeepSeek).
EXCECAO = "C22"

# Gate de qualidade (2026-09-22, `scripts/gate_gemini_classificacao.py`,
# `resultado/auditoria-acuracia/gemini/gate.json`): configuração de produção
# (consenso 2-de-3 + V2 passada única), 100 reviews do gabarito humano.
MODELO = "gemini-3.7-flash"
# Camada das chamadas SÍNCRONAS da exceção (o caminho principal é o batch,
# `scripts/c22_batch.py`; o síncrono só retenta o que falhou nele). Padrão, e
# não Flex, por medição (2026-09-22, sondas de 100 sobre o gabarito): a Flex
# ficou sem capacidade em 35/100 (concorrência 32) e 42/100 (concorrência 8)
# chamadas — cada uma paga a espera de 3 tentativas com 503 e cai na padrão —,
# com latência mediana de 21-30 s contra 2 s. `None` = camada padrão.
CAMADA = None

SLUGS = frozenset({
    "1917",
    "a-fistful-of-dollars",
    "a-quiet-place-2018",
    "aladdin-2019",
    "american-sniper",
    "batman-begins",
    "blackkklansman",
    "bullet-train",
    "conclave",
    "dallas-buyers-club",
    "detachment",
    "eyes-wide-shut",
    "fantastic-mr-fox",
    "for-a-few-dollars-more",
    "ford-v-ferrari",
    "full-metal-jacket",
    "green-book",
    "guardians-of-the-galaxy",
    "harry-potter-and-the-deathly-hallows-part-1",
    "harry-potter-and-the-philosophers-stone",
    "how-to-make-millions-before-grandma-dies",
    "how-to-train-your-dragon",
    "it-was-just-an-accident",
    "kill-bill-vol-2",
    "logan-2017",
    "men-in-black",
    "mid90s",
    "moneyball",
    "perfect-blue",
    "poor-things-2023",
    "project-x-2012",
    "punch-drunk-love",
    "rango",
    "saving-private-ryan",
    "scarface-1983",
    "school-of-rock",
    "scream",
    "snatch",
    "spider-man-into-the-spider-verse",
    "superbad",
    "the-big-lebowski",
    "the-dark-knight",
    "the-dark-knight-rises",
    "the-drama",
    "the-empire-strikes-back",
    "the-good-the-bad-and-the-ugly",
    "the-pursuit-of-happyness",
    "the-simpsons-movie",
    "the-whale-2022",
    "there-will-be-blood",
    "toy-story-3",
    "train-dreams",
    "transformers",
    "vertigo",
    "where-is-the-friends-house",
})


class ForaDaExcecao(ValueError):
    """Slug fora dos 55 pedido sob a exceção."""


def exigir_no_escopo(slugs) -> None:
    fora = sorted(set(slugs) - SLUGS)
    if fora:
        raise ForaDaExcecao(
            f"a exceção C22 (Gemini) vale só para os 55 do lote de 18/09; "
            f"fora dela: {fora}")
