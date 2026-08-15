"""[§D2, v1.9.9] Best-of-3 executado — geração, seleção por código e gate do editor.

Três etapas, uma por entrega:

    rodar       gera N narrativas independentes por filme e seleciona POR
                CÓDIGO (`espectro24.selecao_narrativa`), com retry
                DIRECIONADO quando nenhuma passa limpa (Entrega 5);
    calibracao  imprime as N narrativas de um filme SEM dizer qual o código
                escolheu — a leitura humana vem primeiro, e só depois o
                veredito automático é revelado (Entrega 5);
    gate        imprime a narrativa selecionada de cada filme, SEM passar
                pelo editor [E2], que é o material da decisão de aposentar
                o estágio (Entrega 6).

**O que este script NÃO faz:** dizer qual texto é melhor. A seleção entre
candidatos é mecânica e a escolha de MODELO continua sendo leitura humana.
Nenhum LLM julga prosa aqui — nem o que gerou, nem outro.

O editor [E2] não é chamado em nenhum caminho: é isso que o gate mede.
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
from espectro24 import selecao_narrativa as sn  # noqa: E402
from espectro24 import synthesize as S  # noqa: E402
from espectro24.config import BEST_OF_N, PROSA_MAX_TOKENS  # noqa: E402

SAIDA = RAIZ / "resultado" / "best-of-3"
ARQ = SAIDA / "resultados.json"
FILMES = ("cure", "cidade-de-deus", "the-invite-2026")

# O candidato que fechou 0 flags nos 3 filmes na rodada v1.9.9. A escolha
# FINAL de modelo é do dono do projeto, por leitura — `--modelo` existe
# exatamente para que este script não a congele.
MODELO_PADRAO = ("gemini", "gemini-3.7-flash")


def _gerar(system: str, user: str, provider: str, modelo: str) -> tuple[str, dict, float]:
    t0 = time.time()
    resp = S.resposta(system, user, modelo, provider=provider,
                      max_tokens=PROSA_MAX_TOKENS, json_mode=True)
    bruto = (resp.text if provider == "gemini"
             else resp.choices[0].message.content)
    return br.extrair_narrativa(bruto or ""), S.uso(resp, provider), time.time() - t0


def cmd_rodar(args) -> None:
    from dotenv import load_dotenv
    load_dotenv(RAIZ / ".env")
    SAIDA.mkdir(parents=True, exist_ok=True)
    provider, modelo = args.provider, args.modelo
    dados = json.loads(ARQ.read_text(encoding="utf-8")) if ARQ.exists() else {}

    for slug in FILMES:
        output = json.loads((RAIZ / "resultado" / f"{slug}.json").read_text("utf-8"))
        briefing = br.montar_briefing(output)
        user = br.serializar_briefing(briefing)

        candidatos, telemetria = [], []
        for i in range(BEST_OF_N):
            texto, uso, dt = _gerar(br.PROMPT_NARRADOR_BRIEFING, user, provider, modelo)
            candidatos.append(texto)
            telemetria.append({"uso": uso, "latencia_s": round(dt, 2)})
            print(f"  {slug} #{i}: {dt:.1f}s · {len(texto.split())} palavras")

        escolha = sn.selecionar(candidatos, briefing)
        print(f"  {slug}: escolhido #{escolha['indice']} "
              f"({escolha['motivo']} / {escolha['criterio_decisivo']})")

        # Fallback: nenhuma limpa → retry DIRECIONADO só nas frases
        # infratoras. Descartar as 3 seria jogar fora prosa boa por causa de
        # uma frase.
        retry = None
        if escolha["precisa_retry"]:
            infratoras = sn.frases_infratoras(escolha["narrativa"], briefing)
            print(f"  {slug}: retry direcionado em {len(infratoras)} frase(s)")
            texto, uso, dt = _gerar(br.PROMPT_NARRADOR_BRIEFING,
                                    sn.prompt_retry(escolha["narrativa"], infratoras),
                                    provider, modelo)
            if texto:
                medida = sn.medir(texto, briefing)
                retry = {"frases_infratoras": infratoras, "narrativa": texto,
                         "uso": uso, "latencia_s": round(dt, 2),
                         "n_flags": medida["n_flags"],
                         # a corrigida só entra se REALMENTE melhorar — um
                         # retry que piora não é conserto.
                         "aplicado": medida["n_flags"] < escolha["verificacao"]["n_flags"]}
                if retry["aplicado"]:
                    escolha["narrativa"] = texto
                    escolha["verificacao"] = medida["verificacao"]

        dados[slug] = {"provider": provider, "modelo": modelo,
                       "briefing": briefing, "candidatos": candidatos,
                       "telemetria": telemetria, "escolha": escolha,
                       "retry": retry, "editor_aplicado": False}
        ARQ.write_text(json.dumps(dados, ensure_ascii=False, indent=2), "utf-8")
    print(f"\n→ {ARQ.relative_to(RAIZ)}")


def cmd_calibracao(args) -> None:
    """As N narrativas, EM ORDEM, sem dizer qual o código escolheu.

    A ordem é a de geração (não embaralhada) para que a leitura seja
    reproduzível — o que fica oculto é o veredito, não a identidade.
    """
    dados = json.loads(ARQ.read_text(encoding="utf-8"))
    d = dados[args.slug]
    print("=" * 78)
    print(f"CALIBRAÇÃO DOS PROXIES — {args.slug} · {d['modelo']}")
    print("=" * 78)
    print("Leia as três e escolha a sua preferida ANTES de rodar\n"
          "`best_of_3.py veredito`. Poucos casos não provam que os proxies\n"
          "estão certos; provam, no máximo, que não estão obviamente errados.\n"
          "Um desacordo é resultado publicável: significa que o proxy mede\n"
          "outra coisa que não o que um leitor vê.\n")
    for i, texto in enumerate(d["candidatos"]):
        print(f"\n{'─' * 78}\n### CANDIDATO {chr(65 + i)} · {len(texto.split())} palavras\n")
        print(texto)


def cmd_veredito(args) -> None:
    dados = json.loads(ARQ.read_text(encoding="utf-8"))
    d = dados[args.slug]
    e = d["escolha"]
    print(f"ESCOLHA DO CÓDIGO — {args.slug}: "
          f"CANDIDATO {chr(65 + e['indice'])}")
    print(f"  motivo: {e['motivo']} · critério decisivo: {e['criterio_decisivo']}\n")
    print(f"{'cand':<6}{'flags':>6}{'clichês':>9}{'rep.máx':>9}{'ritmo':>7}"
          f"{'cobertura':>11}")
    for c in e["candidatos"]:
        print(f"{chr(65 + c['indice']):<6}{c['n_flags']:>6}{c['cliches']:>9}"
              f"{c['repeticao_max']:>9}{c['ritmo']:>7}{c['cobertura']:>11.2f}")
    print("\nOrdem dos critérios (só decide entre os de flags limpas): "
          "clichê → repetição → ritmo → cobertura.")


def cmd_gate(args) -> None:
    """As narrativas finais, SEM editor — material da decisão do gate [E2]."""
    dados = json.loads(ARQ.read_text(encoding="utf-8"))
    print("=" * 78)
    print("GATE DO EDITOR [E2] — narrativas finais SEM passar pelo editor")
    print("=" * 78)
    print("Briefing determinístico (v1.9.8) + best-of-3 (v1.9.9), editor NÃO\n"
          "executado. A decisão de aposentar o E2 é do dono do projeto,\n"
          "depois de ler. Se o ritmo faltar, a alternativa já decidida é\n"
          "reescopar o editor por MOVIMENTO — não implementada aqui.\n")
    for slug, d in dados.items():
        e, v = d["escolha"], d["escolha"]["verificacao"]
        print(f"\n{'─' * 78}\n### {slug} · {d['modelo']} · "
              f"{len(e['narrativa'].split())} palavras · {v['n_flags']} flags "
              f"· {v['n_resenha_speak']} clichês · "
              f"{v['n_paragrafos']} parágrafos · editor: NÃO\n")
        print(e["narrativa"])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("etapa", choices=["rodar", "calibracao", "veredito", "gate"])
    ap.add_argument("--slug", default="cure")
    ap.add_argument("--provider", default=MODELO_PADRAO[0])
    ap.add_argument("--modelo", default=MODELO_PADRAO[1])
    args = ap.parse_args()
    {"rodar": cmd_rodar, "calibracao": cmd_calibracao,
     "veredito": cmd_veredito, "gate": cmd_gate}[args.etapa](args)


if __name__ == "__main__":
    main()
