"""[§D2, v1.9.9] Best-of-3 — INVÓLUCRO sobre o narrador de produção.

**v1.9.11: este script não tem mais lógica própria.** Ele delega a
`espectro24.narrador.narrar` — a mesma função que `cli.py` chama em
produção — e existe só pelos comandos de LEITURA (calibração às cegas,
veredito, gate), que não fazem sentido dentro do pipeline. Até a v1.9.10 a
geração e a seleção eram implementadas AQUI, e o pipeline ficou três
versões atrás sem ninguém notar: é esse o defeito que a v1.9.11 corrige, e
manter duas implementações seria repetir a causa.

Quatro etapas:

    rodar       delega ao narrador de produção e grava o resultado dos 3
                filmes (as N narrativas, a escolha e a telemetria);
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

from espectro24 import narrador  # noqa: E402
from espectro24.config import (  # noqa: E402
    MODELO_POR_ESTAGIO,
    PROVIDER_POR_ESTAGIO,
)

SAIDA = RAIZ / "resultado" / "best-of-3"
ARQ = SAIDA / "resultados.json"
FILMES = ("cure", "cidade-de-deus", "the-invite-2026")

# FECHADO (v1.9.10, ver SPEC.md "Fechamento do narrador"): o mesmo valor de
# `MODELO_POR_ESTAGIO["narrativa"]` (config.py) — não duplicado por acaso,
# lido de lá, para que uma mudança futura do modelo de produção não exija
# lembrar de atualizar os dois lugares. `--modelo` continua existindo para
# comparação pontual, sem mexer no default de produção.
MODELO_PADRAO = (PROVIDER_POR_ESTAGIO["narrativa"], MODELO_POR_ESTAGIO["narrativa"])


def cmd_rodar(args) -> None:
    """Gera e seleciona — chamando o MESMO código do pipeline.

    v1.9.11: este comando não tem mais lógica própria. Ele monta o `output`
    a partir do JSON em disco e delega a `narrador.narrar` — a função que
    `cli.py` usa em produção. Duas implementações do mesmo estágio foi
    exatamente o que produziu o defeito que a v1.9.11 corrige (o pipeline
    ficou três versões atrás do que o script fazia); manter as duas seria
    repetir a causa enquanto se corrige o efeito.
    """
    from dotenv import load_dotenv
    load_dotenv(RAIZ / ".env")
    SAIDA.mkdir(parents=True, exist_ok=True)
    dados = json.loads(ARQ.read_text(encoding="utf-8")) if ARQ.exists() else {}

    for slug in FILMES:
        output = json.loads((RAIZ / "resultado" / f"{slug}.json").read_text("utf-8"))
        res = narrador.narrar(output, provider=args.provider, model=args.modelo)
        if res.falhou:
            print(f"  {slug}: ERRO — nenhuma amostra devolveu texto")
            continue
        e = res.escolha
        print(f"  {slug}: {res.n_chamadas} chamada(s) · {res.latencia_s:.1f}s "
              f"· escolhido #{e['indice']} ({e['motivo']}/{e['criterio_decisivo']})"
              + (f" · retry {'aplicado' if res.retry['aplicado'] else 'descartado'}"
                 if res.retry else ""))
        dados[slug] = {
            "provider": res.provider, "modelo": res.modelo,
            "briefing": res.briefing, "candidatos": res.candidatos,
            "escolha": res.escolha, "retry": res.retry,
            "telemetria": {"uso": res.uso, "latencia_s": res.latencia_s,
                           "n_chamadas": res.n_chamadas},
            "editor_aplicado": False,
        }
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
    """As narrativas finais de PRODUÇÃO — briefing determinístico +
    best-of-3, modelo fixado, sem editor (aposentado na v1.9.10)."""
    dados = json.loads(ARQ.read_text(encoding="utf-8"))
    print("=" * 78)
    print("NARRATIVAS DE PRODUÇÃO — briefing determinístico + best-of-3, "
          "editor [E2] aposentado")
    print("=" * 78)
    print("Briefing determinístico (v1.9.8) + correções de prosa (v1.9.9) +\n"
          "cobertura estrutural/parágrafo por grupo (v1.9.10) + best-of-3\n"
          "(seleção por código). Modelo FIXADO em `gemini-3.7-flash`\n"
          "(config.py, MODELO_POR_ESTAGIO). O editor [E2] está APOSENTADO —\n"
          "não roda em nenhum caminho (código em "
          "experimentos-editor-e2-arquivado/).\n")
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
