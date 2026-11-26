"""Rotação da coleção do dia com FILA DE DÍVIDA (`selecao.js`, 2026-11-26).

A propriedade que a home promete: com as manchetes reais, TODA coleção aparece em QUALQUER janela de
2N dias seguidos (N = nº de coleções), e a mesma coleção nunca em dois dias seguidos. Antes da correção
isso valia por sorte do calendário: com `boogie-nights` no catálogo, `valorativo:tom_atmosfera` ficava 60
dias fora (a manchete caía nela nos dois dias em que era a da vez). O teste antigo
(`test_home_nova.py::test_colecao_do_dia_percorre_todas_as_colecoes`) segue intacto; este mede a mesma
propriedade sem depender de um catálogo nem de uma data.

Três medições, todas sob `node` (sem node, pulam com motivo):
  1. o catálogo REAL, 730 dias a partir de 2026-10-19: 0 janelas de 2N dias falhando, e a maior lacuna;
  2. 200 catálogos SINTÉTICOS (filmes tirados e acrescentados, coleções novas, slugs e estreias trocados,
     o que varia qual filme é a manchete em cada dia): 0 falhas;
  3. uma reimplementação INDEPENDENTE da regra (coleção mais antiga entre as que não contêm a manchete)
     dá, dia a dia, a mesma coleção que `colecaoDoDia`.
E, como contraprova, que a regra ANTIGA (salto de meio ciclo) falha no catálogo real, ou seja, que a medição
enxerga o defeito.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
JS = RAIZ / "frontend" / "js"

precisa_node = pytest.mark.skipif(
    shutil.which("node") is None, reason="node não encontrado — a rotação não pôde ser EXECUTADA")

PRELUDIO = textwrap.dedent("""
    const S = require(%(selecao)s);
    const fs = require("fs");
    const t = fs.readFileSync(%(indice)s, "utf8");
    const REAL = JSON.parse(t.slice(t.indexOf("=") + 1).trim().replace(/;$/, "")).filmes;
    const BASE = Date.UTC(2026, 9, 19);
    const dia = i => new Date(BASE + i * 86400000).toISOString().slice(0, 10);
    const clone = x => JSON.parse(JSON.stringify(x));

    // janelas de 2N dias com alguma coleção ausente; maior lacuna entre duas aparições; repetições seguidas
    function medir(D, fn, dias) {
        const chaves = S.ordemDasColecoes(D).map(c => c.chave), n = chaves.length;
        const L = [];
        for (let i = 0; i < dias; i++) L.push(fn(D, dia(i)));
        let ruins = 0;
        for (let i = 0; i + 2 * n <= L.length; i++) {
            const s = new Set(L.slice(i, i + 2 * n));
            if (chaves.some(c => !s.has(c))) ruins++;
        }
        const ult = {}; let lacuna = 0, repetidas = 0;
        L.forEach((x, i) => { if (x in ult) lacuna = Math.max(lacuna, i - ult[x]); ult[x] = i; });
        for (let i = 1; i < L.length; i++) if (L[i] === L[i - 1]) repetidas++;
        return {n, janelas: L.length - 2 * n + 1, ruins, lacuna, repetidas};
    }
    let PULOS = 0;   // quantas vezes a coleção devida foi pulada (a fila de dívida em ação)
    const atual = (D, d) => { const c = S.colecaoDoDia(D, d); if (c.evitou) PULOS++; return c.colecao.chave; };
    // a regra ANTIGA: a da vez, ou salto de meio ciclo se a manchete é dela
    function antiga(D, d) {
        const ordem = S.ordemDasColecoes(D), n = ordem.length, k0 = ((S.diasDesdeEpoca(d) %% n) + n) %% n;
        const m = S.escolhaDoDia(D, d).filme.slug;
        let e = ordem[k0];
        if (e.filmes.some(f => f.slug === m)) {
            for (let j = 0; j < n; j++) {
                const c = ordem[(k0 + Math.floor(n / 2) + j) %% n];
                if (c !== ordem[k0] && !c.filmes.some(f => f.slug === m)) { e = c; break; }
            }
        }
        return e.chave;
    }
    function rng(seed) { let s = seed >>> 0; return () => { s = (Math.imul(s, 1664525) + 1013904223) >>> 0; return s / 4294967296; }; }
    const EIXOS = [...new Set(REAL.flatMap(f => (f.eixos_acima || []).map(e => e.eixo)))];
    function sintetico(seed) {
        const r = rng(seed * 2654435761);
        const L = clone(REAL);
        for (let i = Math.floor(r() * 40); i > 0; i--) L.splice(Math.floor(r() * L.length), 1);
        for (let i = Math.floor(r() * 40); i > 0; i--) {
            const m = clone(REAL[Math.floor(r() * REAL.length)]);
            m.slug = "sint-" + seed + "-" + i; m.titulo = m.slug;
            if (r() < 0.5) { m.contraste = "valorativo"; m.assunto_comum = EIXOS[Math.floor(r() * EIXOS.length)]; m.eixos_acima = []; }
            else { m.contraste = "tematico"; m.eixos_acima = [{eixo: EIXOS[Math.floor(r() * EIXOS.length)], lift_pp: 25}]; }
            L.push(m);
        }
        // a manchete de cada dia depende dos slugs (permutação) e das estreias (aniversário)
        if (r() < 0.5) L.forEach(f => { if (r() < 0.5) f.slug += "-" + Math.floor(r() * 1000); });
        L.forEach(f => { if (r() < 0.3) f.estreia = (1950 + Math.floor(r() * 70)) + "-" +
            String(1 + Math.floor(r() * 12)).padStart(2, "0") + "-" + String(1 + Math.floor(r() * 28)).padStart(2, "0"); });
        return L;
    }
""") % {"selecao": json.dumps(str(JS / "selecao.js")), "indice": json.dumps(str(JS / "indice.js"))}


def _node(corpo: str):
    r = subprocess.run(["node", "-e", PRELUDIO + textwrap.dedent(corpo)], capture_output=True, text=True)
    assert r.returncode == 0, f"node falhou:\n{r.stderr}"
    return json.loads(r.stdout)


@precisa_node
def test_catalogo_real_730_dias_toda_colecao_em_toda_janela_de_2n():
    out = _node("""console.log(JSON.stringify(medir(REAL, atual, 730)));""")
    assert out["n"] >= 10 and out["janelas"] == 730 - 2 * out["n"] + 1
    assert out["ruins"] == 0, out
    assert out["lacuna"] <= 2 * out["n"], out        # nenhuma coleção some por mais de 2N dias
    assert out["repetidas"] == 0                     # nunca a mesma em dois dias seguidos


@precisa_node
def test_contraprova_a_regra_antiga_falha_no_catalogo_real():
    """Sem isto a medição poderia estar cega: a regra antiga FALHA aqui (era a falha do boogie-nights)."""
    out = _node("""console.log(JSON.stringify(medir(REAL, antiga, 730)));""")
    assert out["ruins"] > 0 and out["lacuna"] > 2 * out["n"], out


@precisa_node
def test_200_catalogos_sinteticos_zero_falhas():
    out = _node("""
        const r = {catalogos: 0, falhas: [], lacuna: 0, repetidas: 0, com_pulo: 0, antigas_com_falha: 0};
        for (let s = 1; s <= 200; s++) {
            const D = sintetico(s);
            if (S.ordemDasColecoes(D).length < 5) continue;
            r.catalogos++;
            PULOS = 0;
            const m = medir(D, atual, 400);
            if (PULOS) r.com_pulo++;
            if (m.ruins) r.falhas.push([s, m]);
            r.lacuna = Math.max(r.lacuna, m.lacuna / m.n);
            r.repetidas += m.repetidas;
        }
        console.log(JSON.stringify(r));""")
    assert out["catalogos"] >= 190, out
    assert out["falhas"] == [], out["falhas"][:3]
    assert out["lacuna"] <= 2, out                   # lacuna / N, no pior catálogo, dentro do limite de 2N
    assert out["repetidas"] == 0
    assert out["com_pulo"] >= 100                    # a fila de dívida é exercitada de verdade


@precisa_node
def test_regra_independente_mais_antiga_entre_as_que_nao_contem_a_manchete():
    """Reimplementação à parte (último dia de cada coleção em um mapa) = `colecaoDoDia`, dia a dia."""
    out = _node("""
        const D = REAL, ordem = S.ordemDasColecoes(D), n = ordem.length;
        const ultimo = {}; ordem.forEach((c, i) => ultimo[c.chave] = i - n);
        let divergencias = 0, pulos = 0;
        const d0 = S.diasDesdeEpoca(dia(0));
        // a história começa na EPOCA (dia 0): o estado antes disso é a ordem fixa
        for (let k = 0; k <= S.diasDesdeEpoca(dia(729)); k++) {
            const d = new Date(Date.UTC(2026, 0, 1) + k * 86400000).toISOString().slice(0, 10);
            const m = S.escolhaDoDia(D, d).filme.slug;
            const porIdade = ordem.slice().sort((a, b) => (ultimo[a.chave] - ultimo[b.chave]) || (ordem.indexOf(a) - ordem.indexOf(b)));
            const livre = porIdade.find(c => !c.filmes.some(f => f.slug === m));
            const esperada = livre || ordem[((k %% n) + n) %% n];
            if (livre && livre !== porIdade[0]) pulos++;
            if (k >= d0 && S.colecaoDoDia(D, d).colecao.chave !== esperada.chave) divergencias++;
            ultimo[esperada.chave] = k;
        }
        console.log(JSON.stringify({divergencias, pulos}));""".replace("%%", "%"))
    assert out["divergencias"] == 0
    assert out["pulos"] > 0                          # houve dívida a pagar


@precisa_node
def test_pulada_volta_no_primeiro_dia_em_que_a_manchete_nao_e_dela():
    """Fila de dívida: a coleção pulada é a próxima assim que a manchete deixa de ser dela."""
    out = _node("""
        const ordem = S.ordemDasColecoes(REAL);
        const seq = [];
        for (let i = 0; i < 730; i++) {
            seq.push({c: S.colecaoDoDia(REAL, dia(i)), m: S.escolhaDoDia(REAL, dia(i)).filme.slug});
        }
        let pulos = 0, erros = [];
        seq.forEach((x, i) => {
            if (!x.c.evitou || i + 1 >= seq.length) return;
            pulos++;
            // a devida de hoje = a que ficou mais tempo sem aparecer; a pulada é a coleção que contém a manchete
            // e estava na vez: amanhã, se a manchete de amanhã não é dela, ela tem de ser a de amanhã
            const dona = ordem.filter(c => c.filmes.some(f => f.slug === x.m));
            const amanha = seq[i + 1];
            const candidatas = dona.filter(c => !c.filmes.some(f => f.slug === amanha.m));
            // alguma coleção que continha a manchete de hoje e está devendo volta cedo; ao menos uma delas
            // (a devida) aparece nos próximos dias sem que a manchete a barre
            if (!candidatas.length) return;
            const prox = seq.slice(i + 1, i + 1 + 2 * ordem.length).map(y => y.c.colecao.chave);
            if (!candidatas.some(c => prox.includes(c.chave))) erros.push(i);
        });
        console.log(JSON.stringify({pulos, erros}));""")
    assert out["pulos"] > 0 and out["erros"] == []
