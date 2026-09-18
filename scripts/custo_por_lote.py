"""Custo REAL dos lotes de classificação + verificador, com a tabela de preço e
a janela de pico de `espectro24.preco`. SOMENTE LEITURA: não chama LLM nem
grava nada.

Os registros anteriores a 2026-09-18 não têm `ts`. Sabemos, pelos logs do
driver (`dados/lote/logs-*/00_resumo.log`), a janela de cada ESTÁGIO; dentro
dela as chamadas saem a taxa aproximadamente constante (7/s, medido), então
cada registro é alocado no tempo linearmente pela sua posição no arquivo —
que é a ordem de conclusão, porque os arquivos são append-only. É uma
aproximação declarada, e o erro dela é de segundos por fronteira de janela.

Uso:
    python scripts/custo_por_lote.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from espectro24.preco import (  # noqa: E402
    FORA_DE_PICO,
    PICO,
    TABELA_VERIFICADA_EM,
    aviso_de_validade,
    custo_usd,
    em_pico,
)

VOTACAO = RAIZ / "resultado" / "votacao-3"
UTC = timezone.utc

# Constantes ANTIGAS (14/08), só para mostrar o quanto o código subestimava.
_VELHO = dict(miss=0.14e-6, hit=0.0028e-6, saida=0.28e-6)


def _t(iso: str) -> datetime:
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(UTC)


@dataclass(frozen=True)
class Lote:
    nome: str
    lista: str
    classificacao: tuple[datetime, datetime]
    verificador: tuple[datetime, datetime]


# Janelas de estágio, dos `00_resumo.log` de cada driver.
LOTE_44 = Lote(
    "lote de 44 (2026-09-16)", "dados/lote/lista-expansao-2026-09-15.txt",
    (_t("2026-09-16T05:57:49Z"), _t("2026-09-16T06:39:19Z")),
    (_t("2026-09-16T06:39:19Z"), _t("2026-09-16T06:48:21Z")))
LOTE_55 = Lote(
    "lote de 55 (2026-09-18)", "dados/lote/lista-noturno-2026-09-18.txt",
    (_t("2026-09-18T08:48:29Z"), _t("2026-09-18T09:26:06Z")),
    (_t("2026-09-18T09:26:06Z"), _t("2026-09-18T09:26:07Z")))
# A reverificação das 139 reviews que o 402 deixou pendentes em 16/09: rodou
# depois do depósito, quinta 2026-09-17; horário = mtime dos arquivos de
# produção (14:33 BRT = 17:33 UTC), fora de qualquer janela de pico.
REVERIFICACAO_44 = _t("2026-09-17T17:33:00Z")


def _jsonl(caminho: Path) -> list[dict]:
    return [json.loads(l) for l in caminho.read_text(encoding="utf-8")
            .splitlines() if l.strip()]


def _slugs(lista: str) -> set[str]:
    return {l.split("#")[0].strip() for l in
            (RAIZ / lista).read_text(encoding="utf-8").splitlines()
            if l.split("#")[0].strip()}


def alocar_no_tempo(registros: list[dict], inicio: datetime, fim: datetime
                    ) -> list[tuple[dict, datetime]]:
    """Cada registro no instante `inicio + (i + 0,5)/n × (fim − inicio)`."""
    n = len(registros)
    return [(r, inicio + (fim - inicio) * ((i + 0.5) / n))
            for i, r in enumerate(registros)]


@dataclass
class Custo:
    n: int = 0
    miss: int = 0
    hit: int = 0
    saida: int = 0
    real: float = 0.0            # cada chamada no preço do seu instante
    pico_puro: float = 0.0       # tudo como pico
    fora_puro: float = 0.0       # tudo como fora de pico
    velho: float = 0.0           # as constantes de 14/08
    em_pico_n: int = 0

    def somar(self, uso: dict | None, quando: datetime) -> None:
        if not uso:
            return
        self.n += 1
        self.miss += uso.get("cache_miss_tokens", 0)
        self.hit += uso.get("cache_hit_tokens", 0)
        self.saida += uso.get("completion_tokens", 0)
        self.real += custo_usd(uso, quando)
        self.pico_puro += custo_usd(uso, None)
        self.fora_puro += custo_usd(uso, datetime(2026, 9, 20, 12, tzinfo=UTC))
        self.velho += (uso.get("cache_miss_tokens", 0) * _VELHO["miss"]
                       + uso.get("cache_hit_tokens", 0) * _VELHO["hit"]
                       + uso.get("completion_tokens", 0) * _VELHO["saida"])
        self.em_pico_n += em_pico(quando)


def custo_alocado(alocados: list[tuple[dict, datetime]]) -> Custo:
    c = Custo()
    for r, quando in alocados:
        if r.get("provider", "deepseek") == "deepseek":
            c.somar(r.get("uso"), quando)
    return c


def custo_do_lote(lote: Lote) -> dict:
    slugs = _slugs(lote.lista)
    regs_class = []
    for n in (1, 2, 3):
        regs_class += [r for r in _jsonl(VOTACAO / f"passe_{n}.jsonl")
                       if r.get("slug") in slugs and r.get("ok")]
    id2slug = {}
    for l in _jsonl(VOTACAO / "consenso.jsonl"):
        id2slug[l["id"]] = l["slug"]
    ver = [r for r in _jsonl(VOTACAO / "verificador_producao.jsonl")
           if id2slug.get(r.get("id")) in slugs]
    # Reverificação: id que tem uma falha de SALDO/HTTP antes de um ok.
    falhou_antes, reverificacao, estagio = set(), [], []
    for r in ver:
        if not r["ok"]:
            if "APIStatusError" in r.get("erro", ""):
                falhou_antes.add(r["id"])
            estagio.append(r)
        elif r["id"] in falhou_antes:
            reverificacao.append(r)
        else:
            estagio.append(r)
    out = {
        "lote": lote.nome, "filmes": len(slugs),
        "classificacao": custo_alocado(
            alocar_no_tempo(regs_class, *lote.classificacao)),
        "verificador": custo_alocado(
            alocar_no_tempo(estagio, *lote.verificador)) if estagio else Custo(),
        "reverificacao": custo_alocado(
            [(r, REVERIFICACAO_44) for r in reverificacao]),
        "n_class_ok": len(regs_class),
    }
    return out


def _linha(nome: str, c: Custo, filmes: int) -> str:
    pct = f"{100 * c.em_pico_n / c.n:.0f}%" if c.n else "-"
    return (f"  {nome:<14} {c.n:>6} chamadas · em pico {pct:>4} · "
            f"REAL US${c.real:7.4f} · (tudo pico US${c.pico_puro:.4f} / "
            f"tudo fora US${c.fora_puro:.4f}) · constantes velhas "
            f"US${c.velho:.4f}")


def main() -> int:
    aviso = aviso_de_validade()
    print(f"Tabela: DeepSeek-V4.1-Flash, lida em {TABELA_VERIFICADA_EM}; "
          f"pico US${PICO.entrada_miss}/{PICO.entrada_hit}/{PICO.saida} · "
          f"fora US${FORA_DE_PICO.entrada_miss}/{FORA_DE_PICO.entrada_hit}/"
          f"{FORA_DE_PICO.saida} (miss/hit/saída por M)")
    if aviso:
        print(aviso)
    resultados = {}
    for lote in (LOTE_44, LOTE_55):
        r = custo_do_lote(lote)
        resultados[lote.nome] = r
        total = r["classificacao"].real + r["verificador"].real
        print(f"\n{r['lote']} — {r['filmes']} filmes")
        print(_linha("classificação", r["classificacao"], r["filmes"]))
        print(_linha("verificador", r["verificador"], r["filmes"]))
        if r["reverificacao"].n:
            print(_linha("reverificação", r["reverificacao"], r["filmes"]))
        velho = r["classificacao"].velho + r["verificador"].velho
        print(f"  TOTAL do lote (class.+verif., sem reverificação): "
              f"US${total:.4f}  [constantes velhas dariam US${velho:.4f}; "
              f"razão {total / velho:.2f}×]")

    # Perfil por filme = lote de 44, o único com os TRÊS estágios completos.
    r44 = resultados[LOTE_44.nome]
    f44 = r44["filmes"]
    print("\nPor filme (lote de 44, perfil completo), no regime de preço:")
    perfil = {}
    for nome, sel in (("pico", "pico_puro"), ("fora de pico", "fora_puro")):
        cls = getattr(r44["classificacao"], sel) / f44
        ver = getattr(r44["verificador"], sel) / f44
        perfil[nome] = (cls, ver)
        print(f"  {nome:<13} classificação {cls:.4f} + verificador {ver:.4f} "
              f"= US${cls + ver:.4f}/filme")
    print("\nProjeção para 300 filmes (classificação + verificador, MEDIDA):")
    for nome, (cls, ver) in perfil.items():
        print(f"  {nome:<13} US${300 * (cls + ver):7.2f}")
    print("  (síntese + rotulagem NÃO estão medidas: `uso` delas não é "
          "persistido por filme)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
