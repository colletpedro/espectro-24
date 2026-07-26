#!/usr/bin/env python3
"""Gera DIAGNOSTICO_FLUENCIA.md a partir de resultado/diagnostico_fluencia/.

Só organiza números e textos para leitura humana — NENHUM veredito de
qualidade literária é emitido aqui (a avaliação da prosa é humana, fora da
sessão de diagnóstico).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

IN_DIR = ROOT / "resultado" / "diagnostico_fluencia"
OUT = ROOT / "DIAGNOSTICO_FLUENCIA.md"

ROTULO_COMB = {
    "A": "gemini-2.5-flash · thinking off (baseline de produção)",
    "B": "gemini-2.5-flash · thinking on",
    "C": "gemini-2.5-pro · thinking off",
    "D": "gemini-2.5-pro · thinking on",
}

FLAGS_HONESTIDADE = [
    "quantificador_suspeito", "peso_nao_ancorado", "vocabulario_peso_suspeito",
    "escopo_suspeito", "consenso_suspeito", "perspectiva_nao_marcada",
    "idioma_invalido", "prevalencia_suspeita",
]


def _contaminacao_historica() -> dict:
    """Quantifica a contaminação do few-shot ANTIGO (dados do the-invite)
    nas narrativas da v1.5.0 — evidência que motivou a descontaminação."""
    from diagnostico_fluencia import _shingles
    fewshot_antigo = (
        "Quem gostou é a grande maioria das notas (~79%), e essa turma repete "
        "sempre a mesma dupla: o jeito como Olivia Wilde equilibra comédia e "
        "drama sem deixar nenhum dos dois perder força, e a química do elenco, "
        "que segura o filme inteiro dentro de um apartamento só. No meio-termo, "
        "uma minoria das notas (~18%), o elogio continua — só que até certo "
        "ponto. Para esse grupo as situações começam a se repetir, o filme "
        "estica, e o que era divertido vira cansaço. Já uma pequena minoria "
        "(~3%) não entra na brincadeira em momento nenhum. Para eles o humor é "
        "previsível do começo ao fim, os personagens não passam de caricaturas, "
        "e a sexualidade em cena mais constrange do que provoca."
    )
    out = {}
    for slug in ("the-invite-2026", "cure", "cidade-de-deus"):
        p = ROOT / "resultado" / f"{slug}.json"
        if not p.exists():
            continue
        narr = json.loads(p.read_text(encoding="utf-8")).get("narrativa", "")
        out[slug] = len(_shingles(fewshot_antigo, 8) & _shingles(narr, 8))
    return out


def main() -> int:
    resumo = json.loads((IN_DIR / "_resumo.json").read_text(encoding="utf-8"))
    res = resumo["resultados"]
    L: list[str] = []

    L.append("# Espectro 24 — Diagnóstico de fluência: matriz modelo × thinking")
    L.append("")
    L.append(f"Gerado em {resumo['gerado_em']}. "
             f"**Chamadas Gemini: {resumo['chamadas_gemini']}/{resumo['teto']}.** "
             f"Zero requisições ao Letterboxd e ao TMDB (a síntese vem dos JSONs "
             f"de produção já gerados, no mesmo espírito de `--reuse-synthesis`).")
    L.append("")
    L.append("**Esta é uma sessão de DIAGNÓSTICO, não um bump de versão.** "
             "`SPEC_VERSION` permanece em 1.5.0; os JSONs de produção e o "
             "`frontend/js/data.js` não foram tocados. A única mudança "
             "permanente é a substituição do few-shot (abaixo), que corrige um "
             "defeito metodológico real.")
    L.append("")
    L.append("> **Nenhum veredito de qualidade literária é emitido aqui.** "
             "Este documento reporta números e textos; a avaliação da prosa é "
             "humana e fica fora desta sessão.")
    L.append("")

    # --- contexto/contaminação ---
    L.append("## 1. O problema, e o defeito metodológico que ele escondia")
    L.append("")
    L.append("A v1.5.0 adicionou regras de ritmo/registro e um par few-shot "
             "ANTES/DEPOIS ao §D2. O resultado foi desigual: o `the-invite` "
             "aparentou seguir o estilo novo, enquanto `cure` e "
             "`cidade-de-deus` não transferiram e pioraram em pontos "
             "(períodos emendados, um trecho agramatical no `cure`, \"muitos\" "
             "como sujeito repetido no `cidade-de-deus`).")
    L.append("")
    L.append("**A causa da assimetria não era o modelo — era o exemplo.** O "
             "par ANTES/DEPOIS da v1.5.0 foi escrito com os **dados reais do "
             "`the-invite`** (79%/18%/3%, o nome da diretora, o apartamento "
             "único). Medindo sobreposição de 8-gramas de palavras entre cada "
             "narrativa da v1.5.0 e aquele few-shot — **com as construções "
             "mandatórias mascaradas** (rótulo de peso, marcadores de "
             "perspectiva, enquadramento \"quem gostou\": aparecem por "
             "obrigação de regra, não por cópia):")
    L.append("")
    hist = _contaminacao_historica()
    L.append("| Filme (narrativa v1.5.0) | 8-gramas compartilhados com o few-shot ANTIGO |")
    L.append("|---|---|")
    for slug, n in hist.items():
        L.append(f"| `{slug}` | **{n}** |")
    L.append("")
    L.append("O `the-invite` **copiou o exemplo**, não aprendeu a forma dele. "
             "Os outros dois, sem nada a copiar, não transferiram estilo "
             "nenhum. Um few-shot construído sobre um filme do catálogo "
             "contamina a avaliação daquele filme e só daquele — e por isso "
             "**não media nada**. Sem substituí-lo, a matriz modelo × thinking "
             "mediria o efeito da cópia, não o da condição de execução.")
    L.append("")
    L.append("### Few-shot descontaminado (mudança permanente desta sessão)")
    L.append("")
    L.append("O par foi reescrito com um **filme fictício e números "
             "inventados** (74/19/7), e o prompt agora declara explicitamente "
             "que copiar qualquer fato, adjetivo ou número do exemplo viola a "
             "regra de FIDELIDADE. Dois micro-exemplos que também carregavam "
             "dados do `the-invite` foram neutralizados junto — a regra (e) de "
             "REGISTRO (`\"~79%\"` + \"sem sair de um apartamento\", que é a "
             "ambientação real daquele filme) e a ilustração da ANCORAGEM na "
             "marcação de perspectiva. Um teste novo "
             "(`test_few_shot_nao_usa_dados_de_nenhum_filme_do_catalogo`) "
             "impede a reintrodução de nomes ou shares do catálogo.")
    L.append("")
    L.append("**Validação do detector de contaminação** (contra verdade "
             "conhecida, antes de gastar qualquer chamada da matriz): "
             "`the-invite` v1.5.0 × few-shot ANTIGO → 58 n-gramas "
             "(contaminação real detectada); `the-invite` v1.5.0 × few-shot "
             "NOVO → 0; `cure` × few-shot ANTIGO → 0; few-shot NOVO contra si "
             "mesmo → 73 (o detector dispara quando deve).")
    L.append("")

    # --- cobertura da matriz ---
    pulados = [r for r in res if r.get("pulado")]
    L.append("## 2. Cobertura da matriz — metade NÃO foi obtida")
    L.append("")
    if pulados:
        L.append("**As 4 células de `gemini-2.5-pro` (combinações C e D) "
                 "falharam — o eixo MODELO da matriz não pôde ser testado.** "
                 "Não é rate limit transitório: a API responde `RESOURCE_"
                 "EXHAUSTED` com **`limit: 0`** para `gemini-2.5-pro`, tanto "
                 "em requisições quanto em tokens de entrada, nas cotas por "
                 "minuto **e** por dia. Ou seja, a chave/plano em uso não tem "
                 "acesso ao modelo — repetir a tentativa não muda o resultado. "
                 "Cada célula gastou 2 chamadas (tentativa + 1 backoff de 60s "
                 "conforme o protocolo) antes de ser pulada.")
        L.append("")
        L.append("| Comb. | Filme | Motivo |")
        L.append("|---|---|---|")
        for r in pulados:
            motivo = str(r.get("motivo", "?"))
            if "limit: 0" in motivo or "RESOURCE_EXHAUSTED" in motivo:
                curto = "429 RESOURCE_EXHAUSTED — `limit: 0` para gemini-2.5-pro (sem acesso no plano)"
            elif "orçamento" in motivo:
                curto = "orçamento de 16 chamadas esgotado (após os 429 das células anteriores)"
            else:
                curto = motivo[:120]
            L.append(f"| {r['combinacao']} | `{r['slug']}` | {curto} |")
        L.append("")
        L.append("**Consequência para o diagnóstico:** a hipótese \"o "
                 "`gemini-2.5-flash` não tem capacidade de prosa suficiente\" "
                 "**permanece não testada**. O que esta sessão mede é "
                 "exclusivamente o eixo THINKING, dentro do `gemini-2.5-flash` "
                 "(A vs. B). Concluir qualquer coisa sobre modelo maior a "
                 "partir daqui seria extrapolação sem dado.")
        L.append("")

    # --- tabela-resumo ---
    L.append("## 3. Tabela-resumo — as combinações executadas")
    L.append("")
    L.append("| Comb. | Modelo | Thinking | Filme | n_frases | media_pal | "
             "cv_compr | frase_curta | abert_rep | reporte | -mente | "
             "fluencia_baixa | retentativa | latência (s) | contaminação |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in res:
        if r.get("pulado"):
            motivo = str(r.get("motivo", "?"))
            curto = ("PULADO — 429 `limit: 0`" if "RESOURCE_EXHAUSTED" in motivo
                     else "PULADO — orçamento esgotado")
            L.append(f"| {r['combinacao']} | {r['modelo']} | {r['thinking']} | "
                     f"`{r['slug']}` | — | — | — | — | — | — | — | "
                     f"{curto} | — | — | — |")
            continue
        m = r["metricas_fluencia"]
        L.append(
            f"| {r['combinacao']} | {r['modelo']} | {r['thinking']} | "
            f"`{r['slug']}` | {m['n_frases']} | {m['media_palavras']} | "
            f"**{m['cv_comprimento']}** | **{m['frase_mais_curta']}** | "
            f"{m['aberturas_repetidas']} | {m['verbos_reporte']} | "
            f"{m['adverbios_mente']} | {r['flags']['fluencia_baixa']} | "
            f"{r['houve_retentativa']} | {r['latencia_total_s']} | "
            f"{r['contaminacao_detectada']} |")
    L.append("")
    L.append("Gatilhos de `fluencia_baixa` (§D2): `cv_comprimento < 0.40` · "
             "`frase_mais_curta > 10` · `verbos_reporte > 3` · "
             "`adverbios_mente > 1` · `aberturas_repetidas > 0`.")
    L.append("")

    # --- delta A vs B (o único eixo efetivamente testado) ---
    por = {(r["combinacao"], r["slug"]): r for r in res if not r.get("pulado")}
    L.append("### Delta A → B (thinking off → on), o único eixo testado")
    L.append("")
    L.append("| Filme | métrica | A (off) | B (on) | Δ |")
    L.append("|---|---|---|---|---|")
    for slug in ("the-invite-2026", "cure"):
        a, b = por.get(("A", slug)), por.get(("B", slug))
        if not (a and b):
            continue
        for chave in ("cv_comprimento", "frase_mais_curta", "verbos_reporte",
                      "adverbios_mente", "aberturas_repetidas", "media_palavras",
                      "n_frases"):
            va, vb = a["metricas_fluencia"][chave], b["metricas_fluencia"][chave]
            d = round(vb - va, 2)
            seta = "→" if d == 0 else ("↑" if d > 0 else "↓")
            L.append(f"| `{slug}` | {chave} | {va} | {vb} | {seta} {d:+} |")
        L.append(f"| `{slug}` | latência (s) | {a['latencia_total_s']} | "
                 f"{b['latencia_total_s']} | "
                 f"↑ +{round(b['latencia_total_s'] - a['latencia_total_s'], 1)} |")
    L.append("")
    L.append("**Tokens de thinking efetivamente gastos** (prova de que o "
             "parâmetro fez efeito, e não só de que foi aceito):")
    L.append("")
    L.append("| Comb. | Filme | thinking_tokens | output_tokens | max_output_tokens | finish_reason |")
    L.append("|---|---|---|---|---|---|")
    for comb in ("A", "B"):
        for slug in ("the-invite-2026", "cure"):
            r = por.get((comb, slug))
            if not r:
                continue
            u = (r["chamadas"][-1].get("usage") or {}) if r["chamadas"] else {}
            L.append(f"| {comb} | `{slug}` | {u.get('thinking_tokens')} | "
                     f"{u.get('output_tokens')} | {r['max_output_tokens']} | "
                     f"{r['chamadas'][-1].get('finish_reason')} |")
    L.append("")
    L.append("O consumo de 5.1k-7.7k tokens de thinking **confirma "
             "retroativamente o diagnóstico da v1.2.x**: sob o teto de 3000 da "
             "configuração de produção, thinking sozinho estouraria o "
             "orçamento e cortaria o JSON no meio — exatamente o motivo de "
             "`thinking_budget=0` ter sido fixado.")
    L.append("")
    L.append("**Mas 8000 também não bastou.** Detalhe por chamada (cada célula "
             "faz 1 chamada + retentativas do §D2):")
    L.append("")
    L.append("| Comb. | Filme | # | finish_reason | json_válido | thinking_tok | output_tok |")
    L.append("|---|---|---|---|---|---|---|")
    for comb in ("A", "B"):
        for slug in ("the-invite-2026", "cure"):
            r = por.get((comb, slug))
            if not r:
                continue
            for i, c in enumerate(r["chamadas"], 1):
                u = c.get("usage") or {}
                L.append(f"| {comb} | `{slug}` | {i} | {c.get('finish_reason')} | "
                         f"{c.get('json_valido')} | {u.get('thinking_tokens')} | "
                         f"{u.get('output_tokens')} |")
    L.append("")
    L.append("Nas DUAS células com thinking, ao menos uma chamada morreu em "
             "`MAX_TOKENS` com JSON inválido — thinking chegou a **7676 tokens "
             "(96% do teto de 8000)**, deixando ~300 para a resposta. As "
             "consequências são operacionais, não estéticas:")
    L.append("")
    L.append("- **B · `the-invite`**: a 1ª chamada foi truncada, gastando a "
             "retentativa-de-JSON do §D2; a célula precisou de **3 chamadas** "
             "em vez de 2.")
    L.append("- **B · `cure`**: foi a **retentativa de validação** que morreu "
             "truncada. Como `_uma_chamada` devolve `None` em JSON inválido, o "
             "pipeline descartou a correção e **manteve a resposta original** "
             "(degradação segura, por construção) — mas isso significa que a "
             "tentativa de corrigir `perspectiva_nao_marcada` foi perdida em "
             "silêncio, e a flag ficou marcada por truncamento, não por "
             "teimosia do modelo.")
    L.append("")
    L.append("Consequência prática para quem for adotar thinking: o teto "
             "precisa ser dimensionado para **thinking + JSON completo** "
             "(~7.7k + ~1.1k observados ⇒ folga real a partir de ~12000), e o "
             "custo do thinking **cresce na retentativa** (o reforço alonga o "
             "prompt: 5153 → 7576 tokens no `cure`) — justamente quando o "
             "orçamento já está mais apertado.")
    L.append("")

    # --- flags de honestidade ---
    L.append("## 4. Flags de honestidade sob cada condição")
    L.append("")
    L.append("| Comb. | Filme | " + " | ".join(FLAGS_HONESTIDADE) + " |")
    L.append("|---|---|" + "|".join(["---"] * len(FLAGS_HONESTIDADE)) + "|")
    for r in res:
        if r.get("pulado"):
            continue
        vals = " | ".join(str(r["flags"].get(f)) for f in FLAGS_HONESTIDADE)
        L.append(f"| {r['combinacao']} | `{r['slug']}` | {vals} |")
    L.append("")
    todas = [r for r in res if not r.get("pulado")]
    piores = [(r["combinacao"], r["slug"], f) for r in todas
              for f in FLAGS_HONESTIDADE if r["flags"].get(f)]
    if piores:
        L.append("**Flags acionadas:**")
        for comb, slug, f in piores:
            L.append(f"- {comb} · `{slug}`: `{f}`")
        L.append("")
        L.append("**Leitura honesta deste quadro — thinking NÃO saiu neutro.** "
                 "As invariantes numéricas centrais (quantificador, ancoragem "
                 "de peso, vocabulário \"das notas\", escopo, consensos, "
                 "idioma) ficaram **limpas em todas as 4 células executadas** — "
                 "nem thinking as degradou. Mas `perspectiva_nao_marcada` "
                 "**apareceu só com thinking (B), nos dois filmes**, e estava "
                 "ausente no baseline (A). Antes de atribuir isso ao "
                 "raciocínio do modelo, vale a causa mecânica documentada "
                 "acima: no `cure` a retentativa que corrigiria a marcação "
                 "morreu em `MAX_TOKENS` e foi descartada. Ou seja, parte "
                 "desse resultado é **efeito do teto de tokens**, não do "
                 "thinking em si — e separar as duas coisas exige repetir B "
                 "com um teto folgado (~12000), o que esta sessão não fez.")
    else:
        L.append("**Nenhuma flag de honestidade foi acionada em nenhuma "
                 "combinação** — nem com thinking habilitado, nem com o modelo "
                 "maior.")
    L.append("")

    # --- narrativas ---
    L.append("## 5. As narrativas, na íntegra")
    L.append("")
    for comb in ("A", "B", "C", "D"):
        L.append(f"### Combinação {comb} — {ROTULO_COMB[comb]}")
        L.append("")
        for r in res:
            if r["combinacao"] != comb:
                continue
            L.append(f"#### `{r['slug']}`")
            L.append("")
            if r.get("pulado"):
                L.append(f"_PULADO: {r.get('motivo','?')}_")
                L.append("")
                continue
            m = r["metricas_fluencia"]
            ch = r["chamadas"][-1] if r["chamadas"] else {}
            usage = ch.get("usage") or {}
            L.append(f"- `n_palavras`: {r['n_palavras']} · "
                     f"`max_output_tokens`: {r['max_output_tokens']} · "
                     f"`finish_reason`: {ch.get('finish_reason')} · "
                     f"latência: {r['latencia_total_s']}s · "
                     f"chamadas LLM: {r['n_chamadas_llm']}")
            if usage:
                L.append(f"- tokens — prompt: {usage.get('prompt_tokens')}, "
                         f"saída: {usage.get('output_tokens')}, "
                         f"thinking: {usage.get('thinking_tokens')}")
            L.append(f"- métricas: {json.dumps(m, ensure_ascii=False)}")
            L.append(f"- `contaminacao_detectada`: **{r['contaminacao_detectada']}**")
            if r["contaminacao_detectada"]:
                L.append(f"  - n-gramas: {r['n_gramas_compartilhados']}")
            if r["houve_retentativa"]:
                gat = [f for f in ("fluencia_baixa", "perspectiva_nao_marcada",
                                   *FLAGS_HONESTIDADE) if r["flags"].get(f)]
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
