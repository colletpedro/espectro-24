"""Experimento 7 (não-versão): narrador [D2] e editor [E2] no Ollama local.

NÃO faz parte da spec/pipeline de produção. Roda inteiramente sobre os JSONs
já sintetizados de `cure` e `cidade-de-deus` (gabaritos Gemini,
`resultado/*.json`) — não coleta nada do Letterboxd, não chama Gemini/TMDB.

Orçamento: máximo 12 chamadas Ollama reais no processo inteiro (narrador +
editor, todos os filmes e condições). Um contador global e um teto de
segurança (`ORCAMENTO_MAX`) garantem que nenhuma chamada além da 12ª bata na
rede: a partir da 13ª tentativa, o wrapper devolve "" sem chamar o Ollama,
simulando "provider indisponível" — o mesmo caminho de falha graciosa que o
código de produção já tem para JSON inválido / editor sem resposta.

Para caber no orçamento com margem para retentativa real, o teto de
retentativas do EDITOR é reduzido de EDITOR_MAX_TENTATIVAS=3 (produção) para
1, só neste processo (monkeypatch da constante no módulo `synthesize`, não
no arquivo `config.py`) — decisão documentada no relatório. O narrador já
tem só 1 retentativa fixa no código, não configurável.

Pior caso de chamadas com esse teto:
  narrador:  2 filmes x (1 chamada + até 1 retentativa) = até 4
  editor:    4 invocações (B1 x2 filmes, B2 x2 filmes) x (1 + até 1) = até 8
  total:                                                    até 12
"""
from __future__ import annotations

import copy
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from espectro24 import synthesize as syn  # noqa: E402
from espectro24.models import NarrativaResult  # noqa: E402

ORCAMENTO_MAX = 12
MODEL = "qwen3-espectro"

ESTADO = {"chamadas": 0, "log": []}


def ollama_contado(system: str, user: str, model: str) -> str:
    """Wrapper de `ollama_client_call` que conta chamadas reais, respeita o
    orçamento de 12, e mede tempo por chamada."""
    if ESTADO["chamadas"] >= ORCAMENTO_MAX:
        ESTADO["log"].append({
            "chamada_n": ESTADO["chamadas"] + 1,
            "pulada_por_orcamento": True,
            "tempo_s": 0.0,
        })
        print(f"  [ORÇAMENTO ESGOTADO] chamada pulada (>= {ORCAMENTO_MAX})",
              file=sys.stderr)
        return ""
    ESTADO["chamadas"] += 1
    n = ESTADO["chamadas"]
    t0 = time.monotonic()
    try:
        raw = syn.ollama_client_call(system, user, model)
        dt = time.monotonic() - t0
        ESTADO["log"].append({"chamada_n": n, "pulada_por_orcamento": False,
                              "tempo_s": round(dt, 1), "erro": None})
        print(f"  [chamada {n}/{ORCAMENTO_MAX}] {dt:.1f}s, "
              f"{len(raw)} chars", file=sys.stderr)
        return raw
    except syn.LLMError as e:
        dt = time.monotonic() - t0
        ESTADO["log"].append({"chamada_n": n, "pulada_por_orcamento": False,
                              "tempo_s": round(dt, 1), "erro": str(e)})
        print(f"  [chamada {n}/{ORCAMENTO_MAX}] ERRO após {dt:.1f}s: {e}",
              file=sys.stderr)
        return ""


def carregar_gabarito(slug: str) -> dict:
    return json.loads((ROOT / "resultado" / f"{slug}.json").read_text(encoding="utf-8"))


def rodar_narrador(slug: str, output_gabarito: dict) -> dict:
    """TESTE A — narrador local sobre o output já sintetizado (buckets do
    gabarito). Retorna dict serializável com narrativa gerada + telemetria +
    comparação com o gabarito."""
    output_para_narrador = copy.deepcopy(output_gabarito)
    n_antes = ESTADO["chamadas"]
    t0 = time.monotonic()
    res: NarrativaResult = syn.narrate_output(
        output_para_narrador, client_call=ollama_contado, model=MODEL)
    dt_total = time.monotonic() - t0
    n_chamadas = ESTADO["chamadas"] - n_antes

    resultado = {
        "slug": slug,
        "narrativa_gerada": res.texto,
        "narrativa_bruta_gabarito_gemini": output_gabarito.get("narrativa_bruta"),
        "flags": {
            "idioma_invalido": res.idioma_invalido,
            "escopo_suspeito": res.escopo_suspeito,
            "prevalencia_suspeita": res.prevalencia_suspeita,
            "quantificador_suspeito": res.quantificador_suspeito,
            "consenso_suspeito": res.consenso_suspeito,
            "peso_nao_ancorado": res.peso_nao_ancorado,
            "vocabulario_peso_suspeito": res.vocabulario_peso_suspeito,
            "perspectiva_nao_marcada": res.perspectiva_nao_marcada,
            "aspas_removidas": res.aspas_removidas,
            "falhou": res.falhou,
        },
        "consensos_usados": res.consensos_usados,
        "quantificadores_usados": res.quantificadores_usados,
        "marcadores_perspectiva": res.marcadores_perspectiva,
        "metricas_fluencia": res.metricas_fluencia,
        "n_chamadas_ollama": n_chamadas,
        "houve_retentativa": n_chamadas > 1,
        "tempo_total_s": round(dt_total, 1),
    }
    return resultado, res


def rodar_editor(slug: str, condicao: str, narrativa_result: NarrativaResult,
                 output_gabarito: dict) -> dict:
    """TESTE B — editor local. `condicao` é "B1" (sobre a bruta do gabarito
    Gemini) ou "B2" (sobre a saída do narrador local)."""
    protegidos = syn.montar_protegidos(narrativa_result, output_gabarito)
    n_antes = ESTADO["chamadas"]
    t0 = time.monotonic()
    ed = syn.editar_narrativa(
        narrativa_result, protegidos, output=output_gabarito,
        client_call=ollama_contado, model=MODEL)
    dt_total = time.monotonic() - t0
    n_chamadas = ESTADO["chamadas"] - n_antes

    entrada = narrativa_result.texto or ""
    resultado = {
        "slug": slug,
        "condicao": condicao,
        "texto_entrada": entrada,
        "texto_editado": ed.texto,
        "edicao_flags": {
            "edicao_descartada": ed.edicao_descartada,
            "motivo_descarte": ed.motivo_descarte,
            "protegidos_perdidos": ed.protegidos_perdidos,
            "numeros_alterados": ed.numeros_alterados,
            "houve_retentativa": ed.houve_retentativa,
            "n_tentativas": ed.n_tentativas,
            "motivos_por_tentativa": ed.motivos_por_tentativa,
            "n_protegidos": len(protegidos),
            "similaridade": ed.similaridade,
            "capitalizacao_ajustada": ed.capitalizacao_ajustada,
            "falhou": ed.falhou,
        },
        "protegidos": protegidos,
        "metricas_fluencia_entrada": syn._metricas_fluencia(entrada),
        "metricas_fluencia_saida": ed.metricas_fluencia,
        "n_chamadas_ollama": n_chamadas,
        "tempo_total_s": round(dt_total, 1),
    }
    return resultado


def main() -> None:
    slugs = ["cure", "cidade-de-deus"]

    # v7 (experimento): reduz o teto de retentativa do editor de 3 para 1,
    # só neste processo, para caber no orçamento de 12 chamadas — não altera
    # config.py nem o comportamento de produção.
    syn.EDITOR_MAX_TENTATIVAS = 1

    gabaritos = {s: carregar_gabarito(s) for s in slugs}

    narrador_out_dir = ROOT / "resultado" / "experimento_local" / "v7" / "narrador"
    editor_out_dir = ROOT / "resultado" / "experimento_local" / "v7" / "editor"

    resultados_narrador: dict[str, NarrativaResult] = {}

    print("=== TESTE A — narrador local ===", file=sys.stderr)
    for slug in slugs:
        print(f"-- {slug} --", file=sys.stderr)
        resultado, res = rodar_narrador(slug, gabaritos[slug])
        resultados_narrador[slug] = res
        (narrador_out_dir / f"{slug}.json").write_text(
            json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"   -> chamadas={resultado['n_chamadas_ollama']} "
              f"tempo={resultado['tempo_total_s']}s falhou={res.falhou}",
              file=sys.stderr)

    print("\n=== TESTE B — editor local ===", file=sys.stderr)
    for slug in slugs:
        # B1: editor sobre a narrativa_bruta do GABARITO Gemini
        print(f"-- {slug} / B1 (sobre bruta do gabarito Gemini) --", file=sys.stderr)
        bruta_gabarito = gabaritos[slug].get("narrativa_bruta") or ""
        res_b1_entrada = NarrativaResult(texto=bruta_gabarito)
        resultado_b1 = rodar_editor(slug, "B1", res_b1_entrada, gabaritos[slug])
        (editor_out_dir / f"{slug}__B1.json").write_text(
            json.dumps(resultado_b1, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"   -> chamadas={resultado_b1['n_chamadas_ollama']} "
              f"descartada={resultado_b1['edicao_flags']['edicao_descartada']}",
              file=sys.stderr)

        # B2: editor sobre a saída do narrador LOCAL (Teste A)
        print(f"-- {slug} / B2 (sobre narrador local) --", file=sys.stderr)
        res_a = resultados_narrador[slug]
        if not (res_a.texto or "").strip():
            print("   -> PULADO: narrador local não produziu texto (falhou)",
                  file=sys.stderr)
            resultado_b2 = {
                "slug": slug, "condicao": "B2", "pulado": True,
                "motivo": "narrador local não produziu texto utilizável",
            }
        else:
            resultado_b2 = rodar_editor(slug, "B2", res_a, gabaritos[slug])
            print(f"   -> chamadas={resultado_b2['n_chamadas_ollama']} "
                  f"descartada={resultado_b2['edicao_flags']['edicao_descartada']}",
                  file=sys.stderr)
        (editor_out_dir / f"{slug}__B2.json").write_text(
            json.dumps(resultado_b2, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nTOTAL de chamadas Ollama usadas: {ESTADO['chamadas']}/{ORCAMENTO_MAX}",
          file=sys.stderr)
    (ROOT / "resultado" / "experimento_local" / "v7" / "log_chamadas.json").write_text(
        json.dumps(ESTADO, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
