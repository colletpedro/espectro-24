"""[v1.9.14, Entregas 2-4; reexecutado na v1.9.15 pós-unificação] Acrescenta
o bloco `eixos` a um `resultado/*.json` JÁ PUBLICADO, sem re-rodar síntese
nem narrativa.

**Por que existe, em vez de simplesmente rodar o pipeline de novo.** As
narrativas dos 3 filmes do catálogo passaram no gate de leitura humana do
dono do projeto (v1.9.13). Re-sintetizar mudaria os temas, e regenerar a
narrativa mudaria o texto aprovado — invalidando o gate para economizar
frações de centavo. Este caminho toca SÓ o que é novo: a rotulagem [D3] (1
chamada por bucket) e o bloco de eixos (0 chamadas, é `Counter`).

**Consequência declarada:** o arquivo passa a ter dois carimbos de versão —
`spec_version` no topo (a versão que produziu a narrativa) e
`eixos.spec_version` (a que produziu o schema). A divergência é a verdade
sobre o artefato; reescrever o carimbo do topo diria que a narrativa foi
gerada sob uma spec que ela não viu.

Uso:
    python scripts/enriquecer_eixos.py                    # os 3 do catálogo
    python scripts/enriquecer_eixos.py --slug cure
    python scripts/enriquecer_eixos.py --dry-run          # não escreve nada
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from dotenv import load_dotenv  # noqa: E402

from espectro24 import eixos as E  # noqa: E402
from espectro24.bruto import janela_temporal  # noqa: E402
from espectro24.pipeline import amostra_do_bruto, montar_eixos  # noqa: E402

CATALOGO = ["the-invite-2026", "cure", "cidade-de-deus"]
SAIDA = RAIZ / "resultado" / "v1915"
CONFERENCIA = SAIDA / "ROTULAGEM_CONFERENCIA.md"


def enriquecer(slug: str, dry_run: bool = False) -> dict:
    caminho = RAIZ / "resultado" / f"{slug}.json"
    output = json.loads(caminho.read_text(encoding="utf-8"))

    amostra = amostra_do_bruto(slug, coleta=output.get("coleta"),
                               raiz=str(RAIZ / "dados" / "bruto"))
    analisadas = {b: {r.id for r in rs} for b, rs in amostra.items()}

    # Entrega 6: a janela temporal da AMOSTRA ANALISADA, por bucket. Calculada
    # aqui pela mesma função pura do pipeline, sobre as mesmas reviews que a
    # seleção devolve — não é dado novo de coleta, é leitura do bruto.
    for b in output.get("buckets", []):
        rs = amostra.get(b.get("bucket"))
        if rs is not None:
            b["janela_amostra"] = janela_temporal(rs)

    bloco = montar_eixos(slug, output, analisadas)
    if bloco is None:
        print(f"  {slug}: SEM classificação sob a taxonomia corrente — pulado.")
        return {"slug": slug, "bloco": None}

    output["eixos"] = bloco
    if not dry_run:
        caminho.write_text(json.dumps(output, ensure_ascii=False, indent=2),
                           encoding="utf-8")
    rot = bloco["rotulagem"]
    print(f"  {slug}: contraste={bloco['contraste']} · "
          f"{len(bloco['linhas'])} linhas · {rot['n_chamadas']} chamada(s)"
          + (f" · FALHOU: {rot['falharam']}" if rot["falharam"] else ""))
    return {"slug": slug, "bloco": bloco, "output": output}


def _tabela_de_conferencia(resultados: list[dict]) -> str:
    """A mitigação combinada com o dono do projeto: [D3] não é calibrado
    contra gabarito humano, então as ~50 células vão para conferência à mão.
    """
    L = ["# Conferência da rotulagem [D3] — tema → eixo (v1.9.14)", "",
         "**O que conferir:** cada linha diz em qual EIXO a frase de um grupo",
         "vai aparecer. O NÚMERO da célula não sai daqui — ele é a contagem de",
         "reviews classificadas, e um rótulo errado erra a legenda da linha,",
         "nunca a aritmética (§D3).", "",
         "**Por que à mão:** a classificação por review passou por auditoria de",
         "100 reviews, votação de 3 e precisão/recall por eixo. [D3] não passou",
         "por nada disso. São ~50 células; uma passada de olho é muito melhor",
         "que publicar sem validação nenhuma.", ""]
    total = 0
    for r in resultados:
        bloco = r.get("bloco")
        if not bloco:
            continue
        L += [f"## `{r['slug']}` — contraste: **{bloco['contraste']}**", ""]
        por_bucket: dict[str, list[tuple[str, str, str]]] = {}
        for linha in bloco["linhas"]:
            for bucket, cel in linha["por_bucket"].items():
                if cel.get("tema"):
                    por_bucket.setdefault(bucket, []).append(
                        (cel["tema"], linha["eixo"],
                         f"{cel['mencoes']}/{cel['de_n']}"))
        for bucket in ("negativas", "medianas", "positivas"):
            itens = por_bucket.get(bucket)
            if not itens:
                continue
            L += [f"### {bucket}", "",
                  "| tema (o que a síntese escreveu) | eixo atribuído | freq. do eixo |",
                  "|---|---|---|"]
            for tema, eixo, freq in itens:
                L.append(f"| {tema} | `{eixo}` | {freq} |")
                total += 1
            L.append("")
        semtema = [t for linha in bloco["linhas"]
                   for bucket, cel in linha["por_bucket"].items()
                   for t in (cel.get("temas_no_mesmo_eixo") or [])]
        rot = bloco["rotulagem"]
        if rot["fora_da_taxonomia"]:
            L += [f"⚠️ Eixo fora da taxonomia (virou `livre`): "
                  f"`{rot['fora_da_taxonomia']}`", ""]
        if rot["falharam"]:
            L += [f"⚠️ Rotulagem falhou em: {rot['falharam']} — as células "
                  "desses grupos ficam sem frase.", ""]
    L += ["---", "", f"**{total} células para conferir.**", ""]
    return "\n".join(L)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--slug", action="append",
                   help="slug a enriquecer (repetível); default: os 3 do catálogo")
    p.add_argument("--dry-run", action="store_true",
                   help="roda [D3] e mostra o resultado, sem escrever o JSON")
    args = p.parse_args()
    load_dotenv(RAIZ / ".env")

    slugs = args.slug or CATALOGO
    print(f"Enriquecendo {len(slugs)} filme(s) com o bloco `eixos` "
          f"(taxonomia {E.TAXONOMIA_ID}):")
    resultados = [enriquecer(s, dry_run=args.dry_run) for s in slugs]

    if not args.dry_run:
        SAIDA.mkdir(parents=True, exist_ok=True)
        CONFERENCIA.write_text(_tabela_de_conferencia(resultados),
                               encoding="utf-8")
        print(f"\nTabela de conferência: {CONFERENCIA}")


if __name__ == "__main__":
    main()
