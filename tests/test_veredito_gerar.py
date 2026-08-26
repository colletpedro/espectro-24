"""[v1.9.21, §3[V]] Orquestração do estágio: best-of-3, retry, fallback e
telemetria. ZERO rede — `gerar` é injetado, como em `narrador.narrar`.

O padrão de `narrador.narrar()` (§D2, v1.9.11) é REPRODUZIDO aqui, não
reusado: `selecao_narrativa.selecionar()` está acoplado ao formato de três
movimentos (`spans_por_grupo` ancora no `rotulo_peso` literal, `cobertura`
conta cláusulas por span de grupo, `ritmo` exige duas frases). Num texto de
1-2 frases sem rótulo de peso ancorado, esses três critérios nunca desempatam
nada — seria auditoria de aparência, não de fato.

**O que NÃO pode falhar em produção:** nunca ficar sem veredito, e nunca
publicar um veredito inválido. Os dois degraus de fallback (retry direcionado
→ template determinístico) são o que garante as duas coisas ao mesmo tempo, e
é o que a maior parte deste arquivo mede.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from espectro24 import veredito as V  # noqa: E402

from tests.test_veredito_briefing import (  # noqa: E402
    _dois_lados_com_lift, _um_lado_com_lift, _valorativo)

# LIMPO tem de passar limpo nas TRÊS fixtures usadas aqui, e o único eixo que
# as três compartilham é `roteiro_estrutura` — `_um_lado_com_lift` não cita
# `ritmo` e `_valorativo` não cita `tom_atmosfera`, então um texto que os
# mencionasse dispararia `tema_ausente` por motivo CERTO (o briefing daquele
# filme realmente não tem aquele assunto). Descoberto ao rodar os testes
# contra a implementação; é a validação funcionando, não um falso positivo.
LIMPO = ("Quem não recomenda aponta o roteiro; quem recomenda destaca a "
         "mesma estrutura narrativa.")
INVALIDO = "Cerca de 75% dos críticos apontam o ritmo arrastado."


def _gerador(*respostas):
    """`gerar(system, user) -> (texto, uso, latencia_s)`, servindo `respostas`
    em ordem e repetindo a última. Registra as mensagens recebidas."""
    chamadas = []
    fila = list(respostas)

    def gerar(system, user):
        chamadas.append({"system": system, "user": user})
        texto = fila.pop(0) if len(fila) > 1 else fila[0]
        return (texto, {"prompt_tokens": 10, "completion_tokens": 5,
                        "cache_hit_tokens": 0, "cache_miss_tokens": 10}, 0.5)

    gerar.chamadas = chamadas
    return gerar


# ===========================================================================
# Caminho feliz
# ===========================================================================

def test_caminho_feliz_grava_origem_llm_e_a_telemetria():
    out = _dois_lados_com_lift()
    g = _gerador(LIMPO)
    r = V.gerar(out, n=3, gerar=g)

    assert r["origem"] == "llm"
    assert r["texto"] == LIMPO
    assert r["motivo"] == "melhor_entre_limpos"
    assert r["n_candidatos"] == 3 and r["n_chamadas"] == 3
    assert len(g.chamadas) == 3
    assert r["flags"] == []
    assert r["uso"]["completion_tokens"] == 15      # somado nas 3
    assert r["spec_version"]


def test_as_n_chamadas_sao_independentes_e_recebem_o_mesmo_briefing():
    """Best-of-N é N amostras do MESMO briefing — não uma conversa em que a
    segunda vê a primeira."""
    g = _gerador(LIMPO)
    V.gerar(_dois_lados_com_lift(), n=3, gerar=g)
    assert len({c["user"] for c in g.chamadas}) == 1
    assert len({c["system"] for c in g.chamadas}) == 1


def test_o_system_enviado_e_o_prompt_documentado_na_spec():
    g = _gerador(LIMPO)
    V.gerar(_dois_lados_com_lift(), n=1, gerar=g)
    assert g.chamadas[0]["system"] == V.PROMPT_VEREDITO


def test_amostra_vazia_e_PERDIDA_nao_derruba_o_estagio():
    """Mesma política de `narrador.narrar`: um soluço do provider tira aquela
    amostra da disputa; as demais decidem."""
    g = _gerador("", LIMPO, "")
    r = V.gerar(_dois_lados_com_lift(), n=3, gerar=g)
    assert r["origem"] == "llm"
    assert r["texto"] == LIMPO
    assert r["n_candidatos"] == 1 and r["n_chamadas"] == 3


# ===========================================================================
# Degrau 1 — retry direcionado
# ===========================================================================

def test_nenhum_limpo_dispara_retry_com_as_flags_explicadas():
    g = _gerador(INVALIDO, INVALIDO, INVALIDO, LIMPO)
    r = V.gerar(_dois_lados_com_lift(), n=3, gerar=g)

    assert r["origem"] == "llm"
    assert r["texto"] == LIMPO
    assert r["retry"]["aplicado"] is True
    assert len(g.chamadas) == 4
    # o retry precisa DIZER o que reprovou — senão é só outra amostra
    msg = g.chamadas[3]["user"]
    assert "digito" in msg or "algarismo" in msg.lower()
    assert INVALIDO in msg


def test_retry_que_nao_melhora_NAO_e_aplicado():
    """Um retry que piora não é conserto — mesma regra de §D2."""
    pior = 'Os críticos dizem que 75% acham o "ritmo arrastado e cansativo".'
    g = _gerador(INVALIDO, INVALIDO, INVALIDO, pior)
    r = V.gerar(_dois_lados_com_lift(), n=3, gerar=g)
    assert r["retry"]["aplicado"] is False
    assert r["texto"] != pior


# ===========================================================================
# Degrau 2 — o template determinístico
# ===========================================================================

def test_esgotadas_as_tentativas_cai_no_template_e_declara():
    g = _gerador(INVALIDO)
    out = _dois_lados_com_lift()
    r = V.gerar(out, n=3, gerar=g)

    assert r["origem"] == "template_fallback"
    assert r["motivo"] == "template_fallback"
    assert r["texto"] == V.veredito_template(V.montar_briefing(out))
    assert r["flags"], "o fallback tem de registrar POR QUE caiu"


def test_nenhuma_amostra_com_texto_cai_no_template():
    r = V.gerar(_dois_lados_com_lift(), n=3, gerar=_gerador(""))
    assert r["origem"] == "template_fallback"
    assert r["texto"]


def test_o_texto_publicado_NUNCA_e_invalido():
    """A invariante que resume o estágio: qualquer que seja o caminho, o
    `texto` gravado passa nas validações. Se um dia isso falhar, o produto
    publicou um veredito que ele mesmo reprova."""
    for out in (_dois_lados_com_lift(), _um_lado_com_lift(), _valorativo()):
        for respostas in ([LIMPO], [INVALIDO], [""], [INVALIDO, LIMPO]):
            r = V.gerar(out, n=3, gerar=_gerador(*respostas))
            b = V.montar_briefing(out)
            assert r["texto"], "veredito vazio publicado"
            assert not V.validar(r["texto"], b), (
                f"publicou texto inválido: {r['texto']!r}")


def test_filme_sem_eixos_nao_produz_bloco():
    out = _dois_lados_com_lift()
    out.pop("eixos")
    assert V.gerar(out, n=3, gerar=_gerador(LIMPO)) is None


# ===========================================================================
# Prefixo de código — o único número que sobrevive no texto renderizado
# ===========================================================================

def test_o_prefixo_do_meio_dominante_e_concatenado_pelo_CODIGO():
    """Invariante 5 do prompt: o percentual de peso é prefixado FORA do texto
    do modelo. O modelo continua proibido de escrever qualquer algarismo, e
    o número publicado continua vindo do histograma, não dele."""
    out = _um_lado_com_lift()
    for b_, share in zip(out["buckets"], (25, 45, 30)):
        b_["share_real"] = share
    r = V.gerar(out, n=1, gerar=_gerador(LIMPO))

    assert r["prefixo_codigo"] == ("O meio-termo é o maior grupo da recepção "
                                   "(~45% das notas). ")
    assert r["texto"] == r["prefixo_codigo"] + LIMPO
    assert r["texto_modelo"] == LIMPO


def test_sem_meio_dominante_nao_ha_prefixo():
    r = V.gerar(_dois_lados_com_lift(), n=1, gerar=_gerador(LIMPO))
    assert r["prefixo_codigo"] == ""
    assert r["texto"] == LIMPO


def test_a_validacao_de_digito_roda_sobre_o_texto_do_MODELO():
    """Senão o prefixo (que TEM algarismo, e vem do código) reprovaria o
    candidato — a validação estaria medindo a própria correção."""
    out = _um_lado_com_lift()
    for b_, share in zip(out["buckets"], (25, 45, 30)):
        b_["share_real"] = share
    r = V.gerar(out, n=1, gerar=_gerador(LIMPO))
    assert r["origem"] == "llm"
    assert r["flags"] == []


# ===========================================================================
# Provider/modelo — configuração, nunca hardcode
# ===========================================================================

def test_provider_e_modelo_saem_da_configuracao_por_ESTAGIO():
    from espectro24.config import MODELO_POR_ESTAGIO, PROVIDER_POR_ESTAGIO
    assert "veredito" in PROVIDER_POR_ESTAGIO
    assert "veredito" in MODELO_POR_ESTAGIO
    # nunca um alias — alvo móvel torna a comparação irreproduzível e o preço
    # não ancorável (política da v1.9.10)
    assert "latest" not in MODELO_POR_ESTAGIO["veredito"]


def test_modelo_explicito_e_registrado_na_telemetria():
    r = V.gerar(_dois_lados_com_lift(), n=1, gerar=_gerador(LIMPO),
                model="modelo-de-teste", provider="provider-de-teste")
    assert r["modelo"] == "modelo-de-teste"
    assert r["provider"] == "provider-de-teste"


# ===========================================================================
# Telemetria é diagnóstico de produção, não informação de leitor
# ===========================================================================

def test_a_telemetria_e_serializavel_em_json():
    r = V.gerar(_dois_lados_com_lift(), n=3, gerar=_gerador(INVALIDO, LIMPO))
    json.dumps(r, ensure_ascii=False)      # não pode levantar


def test_o_briefing_NAO_entra_no_bloco_gravado():
    """Mesma decisão de `narrador.telemetria_para_json`: o briefing é função
    determinística do próprio output, e gravá-lo dobraria o JSON para
    reproduzir o que já é reproduzível."""
    r = V.gerar(_dois_lados_com_lift(), n=1, gerar=_gerador(LIMPO))
    assert "briefing" not in r


def test_os_textos_perdedores_nao_sao_gravados():
    """Auditoria de escolha precisa dos NÚMEROS de cada candidato, não dos
    textos — guardar 3 vereditos por filme infla o resultado publicado sem
    responder nenhuma pergunta nova."""
    r = V.gerar(_dois_lados_com_lift(), n=3, gerar=_gerador(INVALIDO, LIMPO))
    for c in r["candidatos"]:
        assert set(c) <= {"indice", "n_flags", "flags", "n_palavras",
                          "n_ancoras", "abertura", "abertura_freq",
                          "eliminado"}
