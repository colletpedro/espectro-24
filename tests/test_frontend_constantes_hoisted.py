"""[v1.9.37] TRAVA do defeito do `var` HOISTED em `frontend/js/filme.js`.

**O defeito, e ele aconteceu DUAS vezes neste arco, no mesmo arquivo.**
`var` hoista a DECLARAÇÃO mas não a ATRIBUIÇÃO. Uma constante de módulo
declarada DEPOIS da chamada `render(film)` chega `undefined` dentro das
funções que o render aciona — e o sintoma não é `ReferenceError`, é um
`undefined` silencioso que só estoura quando alguém o indexa.

  · v1.9.26 — o veredito;
  · v1.9.37 — `ABERTURA_DA_COLUNA`, no bloco de condições.

**As duas foram encontradas só por olhar a tela**, com a suíte verde. Uma
delas nem erro de console produziu num primeiro carregamento. Registro sem
trava foi o que falhou as duas vezes — por isso esta.

**A REGRA: constante de módulo lida por `render()` declara-se no TOPO do
arquivo, junto das demais, nunca depois da chamada.**

**Escopo declarado, para que a trava não seja lida como mais forte do que
é.** Este teste é textual, não um parser de JS. Ele checa as constantes de
MÓDULO no nível de indentação do IIFE (`  var NOME = `, NOME em
maiúsculas) — a convenção que o arquivo já usa. Ele NÃO cobre `let`/`const`
(o arquivo é ES5 por decisão de compatibilidade), nem constantes declaradas
dentro de funções (essas não têm o problema: só executam quando a função
roda).
"""
import re
from pathlib import Path

import pytest

FILME_JS = Path(__file__).resolve().parent.parent / "frontend" / "js" / "filme.js"

# `  var NOME_MAIUSCULO = ` no nível do IIFE (dois espaços de indentação).
RE_CONST = re.compile(r"^  var ([A-Z][A-Z0-9_]*)\s*=", re.M)
RE_RENDER = re.compile(r"^  render\(film\);", re.M)


def _fonte():
    return FILME_JS.read_text(encoding="utf-8")


def test_o_arquivo_e_a_chamada_de_render_existem():
    """Guarda contra TRAP VAZIO (lição da v1.9.25): se o arquivo for
    renomeado ou a chamada mudar de forma, este teste passaria a verificar
    nada e continuaria verde. Ele falha aqui, alto, em vez disso."""
    assert FILME_JS.exists(), FILME_JS
    fonte = _fonte()
    assert RE_RENDER.search(fonte), (
        "não achei a chamada `  render(film);` em filme.js — se ela mudou de "
        "forma, ESTE teste virou decorativo e precisa ser reescrito, não "
        "removido")
    assert RE_CONST.search(fonte), (
        "não achei nenhuma constante de módulo `  var NOME = ` — a convenção "
        "do arquivo mudou e a trava deixou de casar com ele")


def test_constantes_de_modulo_usadas_sao_declaradas_antes_do_render():
    fonte = _fonte()
    linha_render = fonte[:RE_RENDER.search(fonte).start()].count("\n") + 1

    tarde = []
    for m in RE_CONST.finditer(fonte):
        nome = m.group(1)
        linha = fonte[:m.start()].count("\n") + 1
        if linha <= linha_render:
            continue
        # Uma constante NUNCA LIDA não pode chegar `undefined` a lugar nenhum.
        # Ela é código morto — problema real, mas outro, e reportado no teste
        # seguinte em vez de confundido com este.
        usos = len(re.findall(rf"(?<![A-Za-z0-9_]){nome}(?![A-Za-z0-9_])", fonte))
        if usos > 1:
            tarde.append((nome, linha))

    assert not tarde, (
        "constante(s) de módulo declarada(s) DEPOIS de `render(film)` (linha "
        f"{linha_render}) e lida(s) durante o render: {tarde}. `var` hoista a "
        "declaração e não a atribuição — elas chegam `undefined` no render. "
        "Mova para o topo do arquivo, junto das outras constantes.")


def test_nao_ha_constante_de_modulo_morta():
    """Encontrada pela mesma varredura: `BANDAS_QUANTIFICADOR` foi declarada
    e nunca lida. Não é o defeito do hoisting (constante não lida não chega
    `undefined` a lugar nenhum), mas é o que a varredura viu de passagem, e
    código que ninguém exercita é pior que ausência — o mesmo argumento que
    tirou o fallback de render do veredito na v1.9.34."""
    fonte = _fonte()
    mortas = []
    for m in RE_CONST.finditer(fonte):
        nome = m.group(1)
        usos = len(re.findall(rf"(?<![A-Za-z0-9_]){nome}(?![A-Za-z0-9_])", fonte))
        if usos == 1:
            mortas.append((nome, fonte[:m.start()].count("\n") + 1))
    if mortas:
        pytest.xfail(f"constante(s) de módulo declarada(s) e nunca lida(s): "
                     f"{mortas} — dívida conhecida, registrada e não corrigida "
                     f"nesta sessão de publicação (fora do escopo).")
