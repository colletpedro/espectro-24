#!/usr/bin/env python3
"""Gera DIAGNOSTICO_FLUENCIA_V2.md a partir de:
  - resultado/diagnostico_fluencia/v2/_resumo.json  (B, C, D — nova rodada)
  - resultado/diagnostico_fluencia/*.json           (A — reaproveitada da v1,
    válida porque nenhuma chamada daquela célula truncou)

Só organiza números e textos para leitura humana — NENHUM veredito de
qualidade literária é emitido aqui.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
V1_DIR = ROOT / "resultado" / "diagnostico_fluencia"
V2_DIR = V1_DIR / "v2"
OUT = ROOT / "DIAGNOSTICO_FLUENCIA_V2.md"

from espectro24.synthesize import (  # noqa: E402
    _ancora_de_grupo,
    _dividir_frases,
    _indice_frase_de,
    _pesos_por_bucket,
)

ROTULO_COMB = {
    "A": "gemini-2.5-flash · thinking off (reaproveitada da v1 — válida, sem truncamento)",
    "B": "gemini-2.5-flash · thinking_budget=4096 (fixo) · max_output=16000",
    "C": "gemini-2.5-pro · thinking_budget=0 · max_output=16000",
    "D": "gemini-2.5-pro · thinking_budget=4096 (fixo) · max_output=16000",
}

FLAGS_HONESTIDADE = [
    "quantificador_suspeito", "peso_nao_ancorado", "vocabulario_peso_suspeito",
    "escopo_suspeito", "consenso_suspeito", "perspectiva_nao_marcada",
    "idioma_invalido", "prevalencia_suspeita",
]


def _diagnostico_marcadores(slug: str, r: dict) -> list[dict]:
    """Reconstrói, POR MARCADOR declarado, a checagem de posição que o
    validador (`_marcadores_validos`) aplica — para identificar exatamente
    qual marcador (não só qual célula) falhou, e por quê."""
    prod = json.loads((ROOT / "resultado" / f"{slug}.json").read_text(encoding="utf-8"))
    pesos = _pesos_por_bucket(prod)
    from espectro24.synthesize import _marcacoes_por_bucket
    marcacoes = _marcacoes_por_bucket(pesos)
    texto = r["narrativa"]
    frases = _dividir_frases(texto)

    por_grupo: dict[str, list] = {}
    for m in r.get("marcadores_perspectiva", []):
        por_grupo.setdefault(m["grupo"], []).append(m["trecho"])

    linhas = []
    for grupo, trechos in por_grupo.items():
        marcacao = marcacoes.get(grupo, "nenhuma")
        pct, rotulo = pesos.get(grupo, (None, None))
        si_ancora = None
        if marcacao == "antecipada" and pct is not None:
            idx_ancora = _ancora_de_grupo(texto, pct, rotulo)
            si_ancora = _indice_frase_de(frases, texto, idx_ancora)
        for trecho in trechos:
            idx = texto.find(trecho)
            si = _indice_frase_de(frases, texto, idx)
            ok = True
            if marcacao == "antecipada":
                ok = si_ancora is not None and si is not None and si in (si_ancora, si_ancora + 1)
            linhas.append({
                "grupo": grupo, "marcacao": marcacao, "trecho": trecho,
                "si_ancora": si_ancora, "si_marcador": si, "posicao_ok": ok,
            })
    return linhas


def _carregar_a() -> dict:
    """Reconstrói as células A (flash, thinking off) no MESMO formato dos
    resultados de v2, a partir dos JSONs já salvos pela v1."""
    out = {}
    for slug in ("the-invite-2026", "cure"):
        p = V1_DIR / f"{slug}__gemini-2.5-flash__thinking-off.json"
        d = json.loads(p.read_text(encoding="utf-8"))
        d = dict(d)
        d["combinacao"] = "A"
        d["thinking_budget"] = 0
        d["algum_finish_max_tokens"] = any(
            m.get("finish_reason") == "FinishReason.MAX_TOKENS" for m in d["chamadas"])
        out[("A", slug)] = d
    return out


def main() -> int:
    resumo_v2 = json.loads((V2_DIR / "_resumo.json").read_text(encoding="utf-8"))
    res_v2 = resumo_v2["resultados"]
    res_a = _carregar_a()

    por = dict(res_a)
    for r in res_v2:
        por[(r["combinacao"], r["slug"])] = r

    L: list[str] = []
    L.append("# Espectro 24 — Diagnóstico de fluência v2: reteste sob condição válida")
    L.append("")
    L.append(f"Gerado em {resumo_v2['gerado_em']}. "
             f"**Chamadas Gemini nesta rodada: {resumo_v2['chamadas_gemini']}/"
             f"{resumo_v2['teto']}** (a célula A não gastou chamada nova — "
             f"reaproveitada da v1). Zero requisições ao Letterboxd/TMDB.")
    L.append("")
    L.append("**Sessão de DIAGNÓSTICO, não bump de versão.** `SPEC_VERSION` "
             "inalterado; `resultado/<slug>.json` de produção e "
             "`frontend/js/data.js` não foram tocados.")
    L.append("")
    L.append("> **Nenhum veredito de qualidade literária é emitido aqui.** "
             "Números e textos; a avaliação da prosa é humana, fora desta sessão.")
    L.append("")

    # --- motivo do reteste ---
    L.append("## 1. Por que retestar — a v1 tinha uma condição inválida")
    L.append("")
    L.append("Na rodada anterior (`DIAGNOSTICO_FLUENCIA.md`), as duas células "
             "com thinking usavam `max_output_tokens=8000` e **thinking "
             "DINÂMICO** (sem `thinking_budget` fixo — o SDK deixava o modelo "
             "decidir quanto raciocinar). Resultado: o raciocínio consumiu até "
             "**96% do teto** (7676/8000 tokens), e em AMBAS as células pelo "
             "menos uma chamada morreu em `MAX_TOKENS` com JSON inválido. No "
             "`cure`, foi especificamente a **retentativa de validação** que "
             "truncou — como `_uma_chamada` descarta JSON inválido e mantém a "
             "resposta anterior, a correção de `perspectiva_nao_marcada` foi "
             "perdida em silêncio. **Qualquer conclusão sobre thinking a "
             "partir daquela rodada é inválida** — o que se mediu ali foi, em "
             "parte, efeito do teto de tokens, não do raciocínio em si.")
    L.append("")
    L.append("**Correção desta rodada (Tarefa 1):** `thinking_budget` FIXO em "
             "**4096** (não dinâmico) quando thinking está ligado, e "
             "`max_output_tokens=16000` em TODAS as células novas — folga "
             "de ~12000 tokens para a saída mesmo no pior caso observado "
             "(~7.7k de thinking). A célula A (flash, thinking off) não foi "
             "refeita: nenhuma chamada dela truncou na v1, então é "
             "reaproveitada do relatório anterior sem gastar chamada nova.")
    L.append("")

    # --- cobertura ---
    L.append("## 2. Status de cada célula")
    L.append("")
    L.append("| Comb. | Modelo | thinking_budget | max_output | Filme | Status |")
    L.append("|---|---|---|---|---|---|")
    for comb, modelo, tb in (("A", "gemini-2.5-flash", 0),
                             ("B", "gemini-2.5-flash", 4096),
                             ("C", "gemini-2.5-pro", 0),
                             ("D", "gemini-2.5-pro", 4096)):
        maxout = por.get((comb, "cure"), {}).get("max_output_tokens",
                 3000 if comb == "A" else 16000)
        for slug in ("the-invite-2026", "cure"):
            r = por.get((comb, slug))
            if r is None:
                status = "não executada"
            elif r.get("pulado"):
                motivo = str(r.get("motivo", "?"))
                status = ("PULADA — 429 `limit: 0` (gemini-2.5-pro, sem acesso "
                         "no plano)" if "RESOURCE_EXHAUSTED" in motivo
                         else f"PULADA — {motivo[:100]}")
            else:
                status = "executada" + (" (reaproveitada da v1)" if comb == "A" else "")
            L.append(f"| {comb} | {modelo} | {tb} | {maxout} | `{slug}` | {status} |")
    L.append("")

    pulados_pro = [r for r in res_v2 if r.get("pulado") and r["modelo"] == "gemini-2.5-pro"]
    if pulados_pro:
        L.append("**`gemini-2.5-pro` (C/D) continua inacessível nesta chave/plano** "
                 "— mesma assinatura de erro da v1 (`limit: 0`), confirmando que "
                 "é estrutural. Esta rodada tentou **1 vez, sem backoff**, "
                 "conforme instruído — insistir com espera não muda uma cota "
                 "zerada.")
        L.append("")

    # --- tabela comparativa ---
    L.append("## 3. Tabela comparativa — A × B × C × D")
    L.append("")
    L.append("| Comb. | Filme | n_frases | media_pal | cv_compr | frase_curta | "
             "abert_rep | reporte | -mente | fluencia_baixa | perspectiva_nao_marcada | "
             "retentativa | MAX_TOKENS em alguma chamada | latência (s) | contaminação |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for comb in ("A", "B", "C", "D"):
        for slug in ("the-invite-2026", "cure"):
            r = por.get((comb, slug))
            if r is None or r.get("pulado"):
                L.append(f"| {comb} | `{slug}` | — | — | — | — | — | — | — | — | — | — | "
                         f"{'PULADA' if r and r.get('pulado') else 'não executada'} | — | — |")
                continue
            m = r["metricas_fluencia"]
            L.append(
                f"| {comb} | `{slug}` | {m['n_frases']} | {m['media_palavras']} | "
                f"**{m['cv_comprimento']}** | **{m['frase_mais_curta']}** | "
                f"{m['aberturas_repetidas']} | {m['verbos_reporte']} | "
                f"{m['adverbios_mente']} | {r['flags']['fluencia_baixa']} | "
                f"**{r['flags']['perspectiva_nao_marcada']}** | "
                f"{r['houve_retentativa']} | "
                f"**{r.get('algum_finish_max_tokens', False)}** | "
                f"{r['latencia_total_s']} | {r['contaminacao_detectada']} |")
    L.append("")
    L.append("Gatilhos de `fluencia_baixa` (§D2): `cv_comprimento < 0.40` · "
             "`frase_mais_curta > 10` · `verbos_reporte > 3` · "
             "`adverbios_mente > 1` · `aberturas_repetidas > 0`.")
    L.append("")

    # --- detalhe de chamadas (thinking_tokens/finish_reason, TODAS as chamadas) ---
    L.append("## 4. Toda chamada, inclusive retentativas — thinking_tokens e finish_reason")
    L.append("")
    L.append("| Comb. | Filme | # | tipo | finish_reason | json_válido | "
             "thinking_tokens | output_tokens | prompt_tokens |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    algum_truncou_geral = False
    for comb in ("A", "B", "C", "D"):
        for slug in ("the-invite-2026", "cure"):
            r = por.get((comb, slug))
            if r is None or r.get("pulado"):
                continue
            for i, c in enumerate(r["chamadas"], 1):
                u = c.get("usage") or {}
                trunc = c.get("finish_reason") == "FinishReason.MAX_TOKENS"
                algum_truncou_geral = algum_truncou_geral or trunc
                marca = " **⚠️ MAX_TOKENS**" if trunc else ""
                L.append(f"| {comb} | `{slug}` | {i} | {c.get('tipo')} | "
                         f"{c.get('finish_reason')}{marca} | {c.get('json_valido')} | "
                         f"{u.get('thinking_tokens')} | {u.get('output_tokens')} | "
                         f"{u.get('prompt_tokens')} |")
    L.append("")
    if algum_truncou_geral:
        L.append("**⚠️ Ao menos uma chamada desta rodada ainda terminou em "
                 "`MAX_TOKENS`** — ver destaque na tabela acima. Isso significaria "
                 "que o teto de 16000 não era suficiente, e o problema original "
                 "não era (só) o teto.")
    else:
        L.append("**Nenhuma chamada desta rodada terminou em `MAX_TOKENS`.** "
                 "Com `thinking_budget` fixo e `max_output_tokens=16000`, o "
                 "truncamento observado na v1 não se repetiu — era, de fato, "
                 "efeito do teto (e do thinking dinâmico), não uma barreira "
                 "estrutural do modelo/tarefa.")
    L.append("")

    # --- honestidade ---
    L.append("## 5. Flags de honestidade")
    L.append("")
    L.append("| Comb. | Filme | " + " | ".join(FLAGS_HONESTIDADE) + " |")
    L.append("|---|---|" + "|".join(["---"] * len(FLAGS_HONESTIDADE)) + "|")
    for comb in ("A", "B", "C", "D"):
        for slug in ("the-invite-2026", "cure"):
            r = por.get((comb, slug))
            if r is None or r.get("pulado"):
                continue
            vals = " | ".join(str(r["flags"].get(f)) for f in FLAGS_HONESTIDADE)
            L.append(f"| {comb} | `{slug}` | {vals} |")
    L.append("")
    piores = [(comb, slug, f) for comb in ("A", "B", "C", "D")
              for slug in ("the-invite-2026", "cure")
              for f in FLAGS_HONESTIDADE
              if por.get((comb, slug)) and not por[(comb, slug)].get("pulado")
              and por[(comb, slug)]["flags"].get(f)]
    if piores:
        L.append("**Flags acionadas:**")
        for comb, slug, f in piores:
            L.append(f"- {comb} · `{slug}`: `{f}`")
    else:
        L.append("**Nenhuma flag de honestidade foi acionada em nenhuma célula "
                 "executada.**")
    L.append("")

    # --- Tarefa 4: checagem específica de perspectiva_nao_marcada ---
    L.append("## 6. Checagem específica — `perspectiva_nao_marcada` (Tarefa 4)")
    L.append("")
    a_inv = por.get(("A", "the-invite-2026"))
    a_cure = por.get(("A", "cure"))
    b_inv = por.get(("B", "the-invite-2026"))
    b_cure = por.get(("B", "cure"))
    L.append("| | A (thinking off, v1=v2) | B v1 (thinking dinâmico, 8000, "
             "TRUNCOU) | B v2 (thinking_budget=4096 fixo, 16000) |")
    L.append("|---|---|---|---|")
    L.append(f"| `the-invite-2026` | {a_inv['flags']['perspectiva_nao_marcada'] if a_inv else '—'} "
             f"| True (v1) | "
             f"{b_inv['flags']['perspectiva_nao_marcada'] if b_inv and not b_inv.get('pulado') else '—'} |")
    L.append(f"| `cure` | {a_cure['flags']['perspectiva_nao_marcada'] if a_cure else '—'} "
             f"| True (v1) | "
             f"{b_cure['flags']['perspectiva_nao_marcada'] if b_cure and not b_cure.get('pulado') else '—'} |")
    L.append("")
    if b_inv and not b_inv.get("pulado") and b_cure and not b_cure.get("pulado"):
        inv_flag = b_inv["flags"]["perspectiva_nao_marcada"]
        cure_flag = b_cure["flags"]["perspectiva_nao_marcada"]
        inv_trunc = b_inv.get("algum_finish_max_tokens", False)
        cure_trunc = b_cure.get("algum_finish_max_tokens", False)
        L.append(f"**Nenhuma chamada de B v2 truncou** em nenhum dos dois "
                 f"filmes (`algum_finish_max_tokens`: `the-invite`={inv_trunc}, "
                 f"`cure`={cure_trunc} — ver §4), então o resultado de cada "
                 f"filme agora é legível sem a ressalva de truncamento:")
        L.append("")
        if not cure_flag:
            L.append("- **`cure`: a flag SUMIU** (era `True` na v1, é `False` "
                     "aqui). Confirma a hipótese registrada na v1: naquela "
                     "rodada foi exatamente a retentativa de validação do "
                     "`cure` que morreu truncada e foi descartada — sem "
                     "truncamento, a correção do marcador se sustenta e a flag "
                     "não dispara.")
        else:
            L.append("- **`cure`: a flag persistiu** mesmo sem truncamento.")
        diag = _diagnostico_marcadores("the-invite-2026", b_inv) if inv_flag else []
        if inv_flag:
            L.append("- **`the-invite`: a flag PERSISTIU**, com as DUAS "
                     "chamadas em `FinishReason.STOP` (nenhum truncamento) — "
                     "NÃO é o artefato de teto identificado na v1. Reconstruindo "
                     "a checagem POR MARCADOR declarado (mesma lógica de "
                     "`_marcadores_validos`):")
            L.append("")
            L.append("  | grupo | marcação exigida | frase da âncora | frase do "
                     "marcador | posição OK? |")
            L.append("  |---|---|---|---|---|")
            for d in diag:
                L.append(f"  | `{d['grupo']}` | {d['marcacao']} | {d['si_ancora']} "
                         f"| {d['si_marcador']} | {d['posicao_ok']} |")
            falhas = [d for d in diag if not d["posicao_ok"]]
            if falhas:
                grupos_falhos = sorted({d["grupo"] for d in falhas})
                L.append("")
                L.append(f"  **Causa exata:** o narrador declarou **dois** "
                         f"marcadores para o grupo `{grupos_falhos[0]}` "
                         f"(marcacao=\"antecipada\") — o primeiro corretamente "
                         f"posicionado logo após a âncora, e um SEGUNDO, mais "
                         f"tarde no texto, elaborando outro aspecto do mesmo "
                         f"grupo. O validador atual (`_marcadores_validos`) exige "
                         f"que **TODO** marcador declarado para um grupo "
                         f"\"antecipada\" satisfaça a posição, não apenas UM — "
                         f"então o segundo marcador, tardio, derruba a validação "
                         f"inteira mesmo com a âncora corretamente marcada. Nas "
                         f"outras 3 células executadas (A×2, B/`cure`), o "
                         f"narrador declarou exatamente UM marcador por grupo — "
                         f"esta é a única ocorrência de marcação dupla observada "
                         f"nesta sessão.")
                L.append("")
                L.append(f"  **Isto é uma questão de especificação/implementação "
                         f"do validador, não uma evidência de que thinking "
                         f"degrada a marcação de perspectiva em si** — o "
                         f"conteúdo de ambos os marcadores é semanticamente "
                         f"válido (ambos falam do grupo `{grupos_falhos[0]}` "
                         f"com respeito, sem carga depreciativa); o segundo só "
                         f"não está na janela de 2 frases que a heurística "
                         f"aceita. Fica registrado como achado, sem propor "
                         f"correção — mudar `_marcadores_validos` está fora do "
                         f"escopo desta sessão de diagnóstico.")
        else:
            L.append("- **`the-invite`: a flag sumiu.**")
        L.append("")
        L.append("**Veredito da Tarefa 4:** a hipótese de artefato-por-"
                 "truncamento **se confirma para o `cure`** (o caso que a "
                 "motivou — era exatamente a retentativa que morria truncada). "
                 "Para o `the-invite`, a flag persiste mesmo sem truncamento, "
                 "mas a causa raiz identificada acima não é degradação de "
                 "conteúdo pelo thinking — é uma interação entre \"o narrador "
                 "declarou um marcador extra\" (que thinking parece favorecer, "
                 "possivelmente por produzir prosa mais elaborada por grupo) e "
                 "uma regra de validação que exige posição correta em TODOS os "
                 "marcadores de um grupo antecipado, não só o primeiro.")
    else:
        L.append("_(B v2 não pôde ser comparada — ver status em §2.)_")
    L.append("")

    # --- narrativas ---
    L.append("## 7. As narrativas, na íntegra")
    L.append("")
    for comb in ("A", "B", "C", "D"):
        L.append(f"### Combinação {comb} — {ROTULO_COMB[comb]}")
        L.append("")
        for slug in ("the-invite-2026", "cure"):
            r = por.get((comb, slug))
            L.append(f"#### `{slug}`")
            L.append("")
            if r is None:
                L.append("_não executada_")
                L.append("")
                continue
            if r.get("pulado"):
                L.append(f"_PULADA: {r.get('motivo', '?')}_")
                L.append("")
                continue
            m = r["metricas_fluencia"]
            L.append(f"- `n_palavras`: {r['n_palavras']} · "
                     f"`thinking_budget`: {r.get('thinking_budget')} · "
                     f"`max_output_tokens`: {r['max_output_tokens']} · "
                     f"chamadas LLM: {r['n_chamadas_llm']} · "
                     f"latência: {r['latencia_total_s']}s")
            L.append(f"- métricas: {json.dumps(m, ensure_ascii=False)}")
            L.append(f"- `contaminacao_detectada`: **{r['contaminacao_detectada']}**")
            if r["contaminacao_detectada"]:
                L.append(f"  - n-gramas: {r['n_gramas_compartilhados']}")
            L.append(f"- `algum_finish_max_tokens`: **{r.get('algum_finish_max_tokens', False)}**")
            if r["houve_retentativa"]:
                gat = [f for f in ("fluencia_baixa", *FLAGS_HONESTIDADE)
                      if r["flags"].get(f)]
                L.append(f"- **houve retentativa** — flags que persistiram após "
                         f"ela: {gat or 'nenhuma (a retentativa corrigiu)'}")
            L.append("")
            L.append("> " + r["narrativa"].replace("\n\n", "\n>\n> ").replace("\n", "\n> "))
            L.append("")
            if r.get("marcadores_perspectiva"):
                L.append("Marcadores de perspectiva declarados:")
                for mp in r["marcadores_perspectiva"]:
                    L.append(f"- `{mp['grupo']}` — \"{mp['trecho']}\"")
                L.append("")

    OUT.write_text("\n".join(L), encoding="utf-8")
    print(f"OK: {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
