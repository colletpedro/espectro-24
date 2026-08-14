"""Aplica correções DECIDIDAS PELO ANOTADOR ao gabarito humano (`leitura.md`).

O gabarito é permanente: ele valida toda variante de prompt futura. Uma
correção errada nele é pior que a inconsistência que ela tenta consertar,
porque passa a ter aparência de régua aplicada. Daí o desenho deste script:
**ele não decide nada.** Recebe uma lista explícita de decisões, valida que
cada uma bate com o arquivo, aplica só o que foi pedido, e reporta o que
mudou. A régua que fundamenta as decisões está em
`resultado/auditoria-acuracia/REGRA_ANOTACAO.md`.

Formato do arquivo de decisões (JSON):

    {
      "descricao": "texto livre, vai para o log da correção",
      "decisoes": [
        {"id": "viewing:1229439522", "remover": ["impacto_emocional"],
         "motivo": "veredicto seco: 'i didn't like it'"},
        {"id": "viewing:1436204229", "adicionar": ["impacto_emocional"],
         "motivo": "'lugnar det mig' — efeito declarado"}
      ]
    }

Validações OBRIGATÓRIAS, todas antes de escrever qualquer byte:
  1. todo `id` pedido existe em `leitura.md`;
  2. todo eixo citado é da taxonomia (ou `livre`);
  3. `remover` só remove o que está de fato marcado, `adicionar` só
     acrescenta o que não está — pedido que já é no-op vira ERRO, não
     silêncio, porque indica lista construída sobre um arquivo diferente;
  4. nenhum id repetido entre decisões;
  5. backup com timestamp antes de escrever;
  6. contagem de checkboxes marcados antes e depois, e conferência de que a
     diferença bate EXATAMENTE com o número de alterações pedidas — é o que
     prova que nenhuma review foi tocada além do pedido.

Uso:
    python scripts/corrigir_gabarito.py decisoes.json           # aplica
    python scripts/corrigir_gabarito.py decisoes.json --simular # só relata
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

from auditoria_acuracia import (  # noqa: E402
    ARQ_LEITURA,
    EIXOS,
    _RE_BLOCO,
    _RE_CHECK,
    ler_anotacoes_humanas,
)

VALIDOS = set(EIXOS) | {"livre"}
ARQ_LOG = RAIZ / "resultado" / "auditoria-acuracia" / "correcoes_aplicadas.json"


def _blocos(texto: str) -> dict[str, tuple[int, int]]:
    """id da review → (início, fim) do trecho que pertence a ela."""
    marcadores = list(_RE_BLOCO.finditer(texto))
    saida = {}
    for i, m in enumerate(marcadores):
        fim = marcadores[i + 1].start() if i + 1 < len(marcadores) else len(texto)
        saida[m.group(2)] = (m.end(), fim)
    return saida


def _contar_marcados(texto: str) -> int:
    return sum(1 for m in _RE_CHECK.finditer(texto)
               if m.group(1).strip().lower() == "x")


def _validar(decisoes: list[dict], anotacoes: dict, blocos: dict) -> list[dict]:
    """Devolve as alterações concretas (id, eixo, de→para) ou levanta."""
    erros, vistos, alteracoes = [], set(), []
    for d in decisoes:
        rid = d.get("id")
        if not rid:
            erros.append(f"decisão sem `id`: {d!r}")
            continue
        if rid in vistos:
            erros.append(f"{rid}: id repetido entre decisões")
            continue
        vistos.add(rid)
        if rid not in blocos:
            erros.append(f"{rid}: id não existe em {ARQ_LEITURA.name}")
            continue

        marcados = set(anotacoes[rid]["eixos"])
        for eixo in d.get("remover", []):
            if eixo not in VALIDOS:
                erros.append(f"{rid}: eixo desconhecido {eixo!r}")
            elif eixo not in marcados:
                erros.append(f"{rid}: pedido para remover {eixo!r}, que NÃO "
                             f"está marcado (marcados: {sorted(marcados)})")
            else:
                alteracoes.append({"id": rid, "eixo": eixo, "acao": "remover",
                                   "motivo": d.get("motivo", "")})
        for eixo in d.get("adicionar", []):
            if eixo not in VALIDOS:
                erros.append(f"{rid}: eixo desconhecido {eixo!r}")
            elif eixo in marcados:
                erros.append(f"{rid}: pedido para adicionar {eixo!r}, que JÁ "
                             f"está marcado")
            else:
                alteracoes.append({"id": rid, "eixo": eixo, "acao": "adicionar",
                                   "motivo": d.get("motivo", "")})
    if erros:
        raise SystemExit("DECISÕES INVÁLIDAS — nada foi escrito:\n  "
                         + "\n  ".join(erros))
    if not alteracoes:
        raise SystemExit("nenhuma alteração a aplicar")
    return alteracoes


def _aplicar_no_bloco(trecho: str, eixo: str, acao: str) -> str:
    """Troca o marcador de UM eixo dentro de UM bloco.

    Regex ancorado no nome exato do eixo e no início de linha: não pode
    casar `impacto_emocional` dentro de outro nome nem tocar o texto da
    review. `livre` carrega o sufixo ` — temas: ...`, preservado como está.
    """
    de, para = ("x", " ") if acao == "remover" else (" ", "x")
    padrao = re.compile(rf"^([-*] \[){re.escape(de)}(\] {re.escape(eixo)}\b)",
                        re.MULTILINE)
    novo, n = padrao.subn(rf"\g<1>{para}\g<2>", trecho, count=1)
    if n != 1:
        raise SystemExit(f"falha ao {acao} {eixo!r}: {n} ocorrências casadas "
                         f"(esperado exatamente 1)")
    return novo


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("decisoes", type=Path)
    ap.add_argument("--simular", action="store_true",
                    help="valida e relata sem escrever")
    args = ap.parse_args()

    spec = json.loads(args.decisoes.read_text(encoding="utf-8"))
    texto = ARQ_LEITURA.read_text(encoding="utf-8")
    anotacoes = ler_anotacoes_humanas()
    blocos = _blocos(texto)

    alteracoes = _validar(spec["decisoes"], anotacoes, blocos)
    marcados_antes = _contar_marcados(texto)
    n_remover = sum(1 for a in alteracoes if a["acao"] == "remover")
    n_adicionar = len(alteracoes) - n_remover
    esperado_depois = marcados_antes - n_remover + n_adicionar

    print(f"{len(blocos)} reviews em {ARQ_LEITURA.name}")
    print(f"checkboxes marcados ANTES: {marcados_antes}")
    print(f"alterações validadas: {len(alteracoes)} "
          f"({n_remover} remoções, {n_adicionar} adições) em "
          f"{len({a['id'] for a in alteracoes})} review(s)")

    if args.simular:
        for a in alteracoes:
            print(f"  [simulado] {a['acao']:<9} {a['eixo']:<20} {a['id']}")
        print(f"checkboxes marcados DEPOIS (previsto): {esperado_depois}")
        return

    backup = ARQ_LEITURA.with_suffix(f".md.bak-{len(list(ARQ_LEITURA.parent.glob('leitura.md.bak-*')))}")
    shutil.copy2(ARQ_LEITURA, backup)
    print(f"backup: {backup.relative_to(RAIZ)}")

    # Aplica de trás para frente para os offsets dos blocos não invalidarem.
    por_id: dict[str, list[dict]] = {}
    for a in alteracoes:
        por_id.setdefault(a["id"], []).append(a)
    novo = texto
    for rid in sorted(por_id, key=lambda r: blocos[r][0], reverse=True):
        ini, fim = blocos[rid]
        trecho = novo[ini:fim]
        for a in por_id[rid]:
            trecho = _aplicar_no_bloco(trecho, a["eixo"], a["acao"])
        novo = novo[:ini] + trecho + novo[fim:]

    marcados_depois = _contar_marcados(novo)
    if marcados_depois != esperado_depois:
        raise SystemExit(
            f"ABORTADO: contagem de checkboxes não bate — esperado "
            f"{esperado_depois}, obtido {marcados_depois}. Nada foi escrito.")

    # Conferência final: nenhuma review além das pedidas pode ter mudado.
    ARQ_LEITURA.write_text(novo, encoding="utf-8")
    depois = ler_anotacoes_humanas()
    mexidas = {rid for rid in anotacoes
               if set(anotacoes[rid]["eixos"]) != set(depois[rid]["eixos"])}
    if mexidas != set(por_id):
        ARQ_LEITURA.write_text(texto, encoding="utf-8")
        raise SystemExit(
            f"ABORTADO e REVERTIDO: reviews alteradas {sorted(mexidas)} != "
            f"pedidas {sorted(por_id)}")

    print(f"checkboxes marcados DEPOIS: {marcados_depois}")
    print(f"reviews alteradas: {len(mexidas)} (exatamente as pedidas)")

    log = json.loads(ARQ_LOG.read_text(encoding="utf-8")) if ARQ_LOG.exists() else []
    log.append({"descricao": spec.get("descricao", ""),
                "backup": str(backup.relative_to(RAIZ)),
                "checkboxes_antes": marcados_antes,
                "checkboxes_depois": marcados_depois,
                "alteracoes": alteracoes})
    ARQ_LOG.write_text(json.dumps(log, ensure_ascii=False, indent=2),
                       encoding="utf-8")
    print(f"→ {ARQ_LOG.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
