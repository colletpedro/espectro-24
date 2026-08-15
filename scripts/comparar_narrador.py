"""[Entrega 4] Narrativa dos 3 filmes sob cada provider/modelo candidato.

Roda o narrador SOB BRIEFING DETERMINÍSTICO (§D2, v1.9.8) nos 3 filmes do
catálogo, para cada candidato da Entrega 3, e aplica as MESMAS verificações
mecânicas a todos (`espectro24.qualidade`).

**O que este script deliberadamente NÃO faz: julgar qual texto é melhor.**
A comparação de QUALIDADE é leitura humana do dono do projeto. Nenhum LLM
julga prosa aqui, e o modelo que gera não avalia a própria saída — as
métricas mecânicas dizem quem PASSOU nas verificações; a escolha entre os
que passaram não é do script.

Candidatos e o critério de seleção (medido na Entrega 3): versão FIXADA (os
aliases `-latest` são alvo móvel — comparação não reproduzível e preço não
ancorável), cobrindo a faixa de custo de um flash barato a um pro caro.

Uso:
    python scripts/comparar_narrador.py rodar     # gera (LLM, centavos)
    python scripts/comparar_narrador.py relatorio # tabela + textos completos

Saídas em `resultado/comparacao-narrador/`.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from espectro24 import briefing as br  # noqa: E402
from espectro24 import qualidade as q  # noqa: E402
from espectro24 import synthesize as S  # noqa: E402
from espectro24.config import PROSA_MAX_TOKENS  # noqa: E402

SAIDA = RAIZ / "resultado" / "comparacao-narrador"
ARQ = SAIDA / "resultados.json"

MAX_TENTATIVAS = 3

FILMES = ("cure", "cidade-de-deus", "the-invite-2026")

# (rótulo, provider, modelo, preço entrada US$/1M, preço saída US$/1M)
# Preços: https://ai.google.dev/gemini-api/docs/pricing (paid tier) e
# config.py para o DeepSeek. O 3.7-flash tem preço promocional até
# 31/12/2026 (US$0,75/3,75); depois vai a 1,50/7,50 — registrado aqui para
# a comparação de custo não envelhecer em silêncio.
CANDIDATOS = [
    ("deepseek-baseline", "deepseek", "deepseek-v4-flash", 0.14, 0.28),
    ("gemini-3.7-flash", "gemini", "gemini-3.7-flash", 0.75, 3.75),
    ("gemini-2.5-flash", "gemini", "gemini-2.5-flash", 0.30, 2.50),
    ("gemini-3.1-pro", "gemini", "gemini-3.1-pro-preview", 2.00, 12.00),
]


def _custo(uso: dict, p_in: float, p_out: float) -> float:
    return (uso["prompt_tokens"] * p_in / 1e6
            + uso["completion_tokens"] * p_out / 1e6)


def cmd_rodar() -> None:
    from dotenv import load_dotenv
    load_dotenv(RAIZ / ".env")
    SAIDA.mkdir(parents=True, exist_ok=True)

    anterior = json.loads(ARQ.read_text(encoding="utf-8")) if ARQ.exists() else {}
    resultados = anterior

    for slug in FILMES:
        arq_filme = RAIZ / "resultado" / f"{slug}.json"
        if not arq_filme.exists():
            print(f"AVISO: {slug}.json ausente — pulado")
            continue
        output = json.loads(arq_filme.read_text(encoding="utf-8"))
        briefing = br.montar_briefing(output)
        user = br.serializar_briefing(briefing)
        resultados.setdefault(slug, {"briefing": briefing, "modelos": {}})

        for rotulo, provider, modelo, p_in, p_out in CANDIDATOS:
            feito = resultados[slug]["modelos"].get(rotulo)
            if feito and feito.get("ok"):
                print(f"  {slug}/{rotulo}: já feito")
                continue
            t0 = time.time()
            try:
                # Retentativa: a Entrega 3 mediu falha TRANSITÓRIA (resposta
                # vazia/truncada) em modelos que reproduzem bem no retry.
                # Sem isto, um soluço do provider vira buraco na comparação e
                # seria lido como defeito do modelo.
                ultima = None
                for tentativa in range(MAX_TENTATIVAS):
                    resp = S.resposta(br.PROMPT_NARRADOR_BRIEFING, user, modelo,
                                      provider=provider,
                                      max_tokens=PROSA_MAX_TOKENS, json_mode=True)
                    bruto = (resp.text if provider == "gemini"
                             else resp.choices[0].message.content)
                    ultima = br.extrair_narrativa(bruto or "")
                    if ultima:
                        break
                    time.sleep(2 * (tentativa + 1))
                dt = time.time() - t0
                uso = S.uso(resp, provider)
                # extrator tolerante (§briefing): o DeepSeek escapa quebra
                # de linha de forma inconsistente na mesma resposta, e o
                # parser estrito descarta prosa perfeitamente boa.
                narrativa = ultima
                if not narrativa:
                    raise ValueError(
                        f"narrativa vazia após {MAX_TENTATIVAS} tentativas")
                registro = {
                    "ok": True, "provider": provider, "modelo": modelo,
                    "latencia_s": round(dt, 2), "uso": uso,
                    "custo_usd": _custo(uso, p_in, p_out),
                    "narrativa": narrativa,
                    "n_palavras": len(narrativa.split()),
                    "verificacao": q.verificar(narrativa, briefing),
                }
                v = registro["verificacao"]
                print(f"  {slug}/{rotulo}: {dt:.1f}s · {registro['n_palavras']}p "
                      f"· {v['n_flags']} flags · {v['n_resenha_speak']} clichês")
            except Exception as e:  # noqa: BLE001
                registro = {"ok": False, "provider": provider, "modelo": modelo,
                            "erro": f"{type(e).__name__}: {e}",
                            "latencia_s": round(time.time() - t0, 2)}
                print(f"  {slug}/{rotulo}: ERRO {registro['erro'][:80]}")
            resultados[slug]["modelos"][rotulo] = registro
            ARQ.write_text(json.dumps(resultados, ensure_ascii=False, indent=2),
                           encoding="utf-8")
    print(f"\n→ {ARQ.relative_to(RAIZ)}")


def cmd_relatorio() -> None:
    dados = json.loads(ARQ.read_text(encoding="utf-8"))
    rotulos = [c[0] for c in CANDIDATOS]

    print("=" * 78)
    print("TABELA MECÂNICA — quem passou nas verificações")
    print("=" * 78)
    print(f"{'filme':<18}{'modelo':<20}{'flags':>6}{'clichês':>8}"
          f"{'palavras':>10}{'lat(s)':>8}{'US$':>10}")
    tot = {r: {"flags": 0, "speak": 0, "custo": 0.0, "lat": 0.0, "n": 0}
           for r in rotulos}
    for slug, d in dados.items():
        for rot in rotulos:
            m = d["modelos"].get(rot)
            if not m:
                continue
            if not m.get("ok"):
                print(f"{slug:<18}{rot:<20}{'ERRO':>6}  {m['erro'][:40]}")
                continue
            v = m["verificacao"]
            print(f"{slug:<18}{rot:<20}{v['n_flags']:>6}{v['n_resenha_speak']:>8}"
                  f"{m['n_palavras']:>10}{m['latencia_s']:>8.1f}"
                  f"{m['custo_usd']:>10.5f}")
            t = tot[rot]
            t["flags"] += v["n_flags"]; t["speak"] += v["n_resenha_speak"]
            t["custo"] += m["custo_usd"]; t["lat"] += m["latencia_s"]; t["n"] += 1

    print("-" * 78)
    print(f"{'TOTAL':<18}{'':<20}{'flags':>6}{'clichês':>8}{'':>10}"
          f"{'lat.méd':>8}{'US$/3':>10}")
    for rot in rotulos:
        t = tot[rot]
        if not t["n"]:
            continue
        print(f"{'':<18}{rot:<20}{t['flags']:>6}{t['speak']:>8}{'':>10}"
              f"{t['lat'] / t['n']:>8.1f}{t['custo']:>10.5f}")

    print("\n" + "=" * 78)
    print("DETALHE DAS FLAGS")
    print("=" * 78)
    for slug, d in dados.items():
        for rot in rotulos:
            m = d["modelos"].get(rot)
            if not m or not m.get("ok"):
                continue
            v = m["verificacao"]
            problemas = []
            if v["formato_invalido"]:
                problemas.append("formato embrulhado")
            if v["numeros_inventados"]:
                problemas.append(f"números inventados: {v['numeros_inventados']}")
            if v["rotulos_faltando"]:
                problemas.append(f"rótulo de peso ausente: {v['rotulos_faltando']}")
            if v["ordem_incorreta"]:
                problemas.append("ordem dos grupos fora do briefing")
            if v["vocabulario_peso"]:
                problemas.append("vocabulário do peso (reviews/público)")
            if v["resenha_speak"]:
                exprs = ", ".join(f"{a['expressao']}×{a['n']}"
                                  for a in v["resenha_speak"])
                problemas.append(f"resenha-speak: {exprs}")
            if problemas:
                print(f"\n{slug} / {rot}:")
                for p in problemas:
                    print(f"  - {p}")

    print("\n" + "=" * 78)
    print("TEXTOS COMPLETOS — a comparação de QUALIDADE é leitura humana.")
    print("Este relatório NÃO diz qual é melhor.")
    print("=" * 78)
    for slug, d in dados.items():
        for rot in rotulos:
            m = d["modelos"].get(rot)
            if not m or not m.get("ok"):
                continue
            v = m["verificacao"]
            print(f"\n{'─' * 78}\n### {slug} · {rot} · {m['n_palavras']} palavras "
                  f"· {v['n_flags']} flags · {v['n_resenha_speak']} clichês\n")
            print(m["narrativa"])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("etapa", choices=["rodar", "relatorio"])
    args = ap.parse_args()
    {"rodar": cmd_rodar, "relatorio": cmd_relatorio}[args.etapa]()


if __name__ == "__main__":
    main()
