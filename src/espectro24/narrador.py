"""[§D2, v1.9.11] O narrador de PRODUÇÃO — briefing determinístico + best-of-3.

**Por que este módulo existe, e o que ele conserta.** Até a v1.9.10 o
pipeline (`cli.py`) chamava `narrate_output` — o narrador PRÉ-briefing
(§D2 v1.2.0–1.9.7) — enquanto o briefing determinístico (v1.9.8), as
correções de tique/parágrafo/movimento 2 (v1.9.9), a cobertura estrutural e
o parágrafo por grupo (v1.9.10) e o best-of-3 existiam apenas em
`scripts/best_of_3.py`, rodando à parte. Consequência medida: **as
narrativas aprovadas na leitura humana não eram as que o produto geraria.**

Este módulo é o caminho ÚNICO. `scripts/best_of_3.py` passa a ser um
invólucro fino sobre ele — duas implementações do mesmo estágio é
exatamente a divergência que produziu o defeito, e mantê-las seria repetir
a causa enquanto se corrige o efeito.

**O que ele faz, em ordem:** monta o briefing (§D2, código decide o que
dizer) → gera `BEST_OF_N` narrativas INDEPENDENTES do mesmo briefing →
seleciona POR CÓDIGO (`selecao_narrativa`) → se nenhuma passar limpa,
seleciona a de menor severidade e faz um retry DIRECIONADO às frases
infratoras.

**Custo declarado: `BEST_OF_N` chamadas por filme** (mais uma no pior caso,
com o retry), contra 1 do narrador antigo. É o preço do best-of-3, aceito
quando ele foi decidido; o que muda aqui é só que agora é pago em produção.

**Nenhum LLM julga prosa** — a seleção é contagem, e o modelo que gera não
avalia a própria saída.
"""
from __future__ import annotations

import time

from . import briefing as br
from . import selecao_narrativa as sn
from . import synthesize as S
from .config import BEST_OF_N, PROSA_MAX_TOKENS
from .models import NarrativaBriefingResult

ESTAGIO = "narrativa"


def _gerar_real(system: str, user: str, *, provider: str, modelo: str):
    """Uma amostra do narrador: `(texto, uso, latencia_s)`.

    Passa pelo ADAPTADOR (`synthesize.resposta`) como todo caminho de LLM do
    projeto — o guard-rail de §3[D] existe porque esta regra já foi
    reintroduzida por engano uma vez. Usa `resposta` (e não `client_call`)
    porque o best-of-3 precisa dos contadores de token: sem eles, o custo de
    3 chamadas por filme seria invisível no JSON.
    """
    t0 = time.time()
    resp = S.resposta(system, user, modelo, provider=provider,
                      max_tokens=PROSA_MAX_TOKENS, json_mode=True)
    bruto = (resp.text if provider == "gemini"
             else resp.choices[0].message.content)
    return (br.extrair_narrativa(bruto or ""), S.uso(resp, provider),
            time.time() - t0)


def _somar(usos: list[dict]) -> dict:
    chaves = ("prompt_tokens", "completion_tokens",
              "cache_hit_tokens", "cache_miss_tokens")
    return {k: sum(u.get(k, 0) for u in usos) for k in chaves}


def narrar(output: dict, *, n: int = BEST_OF_N, provider: str | None = None,
           model: str | None = None, gerar=None) -> NarrativaBriefingResult:
    """A narrativa de produção do filme, com a telemetria da escolha.

    `gerar` é o ponto de injeção dos testes: `(system, user) -> (texto, uso,
    latencia_s)`. Sem ele, resolve provider e modelo POR ESTÁGIO
    (`provider_do_estagio`/`modelo_do_estagio`, v1.9.8) — que até esta
    versão eram configuração escrita, testada e **inerte**: nenhum caminho
    de produção os chamava, e o narrador acabava rodando no provider global.

    Uma amostra vazia (soluço do provider) é uma amostra PERDIDA, não uma
    falha do estágio: ela sai da disputa e as demais decidem. `falhou=True`
    só quando NENHUMA das `n` devolveu texto.
    """
    briefing = br.montar_briefing(output)
    user = br.serializar_briefing(briefing)

    if gerar is None:
        provider = S.provider_do_estagio(ESTAGIO, provider)
        modelo = model or S.modelo_do_estagio(ESTAGIO, provider)

        def gerar(system, msg):  # noqa: F811 — fechado sobre provider/modelo
            return _gerar_real(system, msg, provider=provider, modelo=modelo)
    else:
        provider, modelo = provider or "injetado", model or "injetado"

    candidatos, usos, latencias = [], [], []
    for _ in range(n):
        texto, uso, dt = gerar(br.PROMPT_NARRADOR_BRIEFING, user)
        usos.append(uso)
        latencias.append(dt)
        if texto:
            candidatos.append(texto)

    if not candidatos:
        return NarrativaBriefingResult(
            texto="", falhou=True, briefing=briefing, candidatos=[],
            provider=provider, modelo=modelo, n_chamadas=n,
            uso=_somar(usos), latencia_s=round(sum(latencias), 2))

    escolha = sn.selecionar(candidatos, briefing)

    # Fallback obrigatório: nenhuma limpa → a de MENOR SEVERIDADE, com retry
    # DIRECIONADO só nas frases infratoras. Descartar as N seria jogar fora
    # prosa boa por causa de uma frase.
    retry = None
    if escolha["precisa_retry"]:
        infratoras = sn.frases_infratoras(escolha["narrativa"], briefing)
        texto, uso, dt = gerar(br.PROMPT_NARRADOR_BRIEFING,
                               sn.prompt_retry(escolha["narrativa"], infratoras))
        usos.append(uso)
        latencias.append(dt)
        if texto:
            medida = sn.medir(texto, briefing)
            # A corrigida só entra se REALMENTE melhorar — um retry que
            # piora não é conserto.
            aplicado = medida["n_flags"] < escolha["verificacao"]["n_flags"]
            retry = {"frases_infratoras": infratoras, "narrativa": texto,
                     "n_flags": medida["n_flags"], "aplicado": aplicado}
            if aplicado:
                escolha["narrativa"] = texto
                escolha["verificacao"] = medida["verificacao"]

    return NarrativaBriefingResult(
        texto=escolha["narrativa"], falhou=False, briefing=briefing,
        candidatos=candidatos, escolha=escolha, retry=retry,
        verificacao=escolha["verificacao"], provider=provider, modelo=modelo,
        n_chamadas=len(usos), uso=_somar(usos),
        latencia_s=round(sum(latencias), 2))


def telemetria_para_json(res: NarrativaBriefingResult) -> dict:
    """O bloco `narrativa_selecao` do JSON de resultado.

    O BRIEFING não entra: é função determinística do próprio `output`, e
    gravá-lo dobraria o JSON para reproduzir o que já é reproduzível. Entram
    as MÉTRICAS de cada candidato (não os textos perdedores — auditoria de
    escolha precisa dos números, e guardar 3 narrativas por filme infla o
    resultado publicado sem responder nenhuma pergunta nova).
    """
    e = res.escolha or {}
    return {
        "provider": res.provider,
        "modelo": res.modelo,
        "n_candidatos": len(res.candidatos),
        "n_chamadas": res.n_chamadas,
        "indice_escolhido": e.get("indice"),
        "motivo": e.get("motivo"),
        "criterio_decisivo": e.get("criterio_decisivo"),
        "candidatos": e.get("candidatos", []),
        "retry": ({"n_frases_infratoras": len(res.retry["frases_infratoras"]),
                   "motivos": sorted({m for f in res.retry["frases_infratoras"]
                                      for m in f["motivos"]}),
                   "n_flags_depois": res.retry["n_flags"],
                   "aplicado": res.retry["aplicado"]}
                  if res.retry else None),
        "uso": res.uso,
        "latencia_s": res.latencia_s,
    }
